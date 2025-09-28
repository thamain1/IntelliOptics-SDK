import asyncio
import base64
from io import BytesIO
from typing import Any
from unittest.mock import AsyncMock, Mock

import pytest
from PIL import Image

from intellioptics import AsyncIntelliOptics, ExperimentalApi, IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import (
    ChannelEnum,
    Detector,
    ImageQuery,
    ModeEnum,
    PaginatedDetectorList,
    PaginatedImageQueryList,
    QueryResult,
    ROI,
)


def _make_client() -> IntelliOptics:
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")
    client._http = Mock()
    return client


def _make_async_client() -> tuple[AsyncIntelliOptics, Any]:
    client = AsyncIntelliOptics.__new__(AsyncIntelliOptics)  # type: ignore[call-arg]
    http = type("_Http", (), {})()
    http.post_json = AsyncMock()
    http.get_json = AsyncMock()
    http.delete = AsyncMock()
    http.request_raw = AsyncMock()
    client._http = http  # type: ignore[attr-defined]
    client.experimental = ExperimentalApi(async_client=client)
    return client, http


def _sample_jpeg_bytes() -> bytes:
    buffer = BytesIO()
    Image.new("RGB", (4, 4), color=(128, 64, 32)).save(buffer, format="JPEG")
    return buffer.getvalue()


def test_init_requires_api_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)

    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://api.example.com")


def test_create_detector_builds_payload() -> None:
    client = _make_client()
    client._http.post_json.return_value = {
        "id": "det-123",
        "name": "Inspector",
        "query": "Is it OK?",
        "mode": "BINARY",
    }

    detector = client.create_detector(
        "Inspector",
        "Is it OK?",
        mode=ModeEnum.BINARY,
        confidence_threshold=0.8,
        metadata={"team": "qa"},
    )

    client._http.post_json.assert_called_once()
    args, kwargs = client._http.post_json.call_args
    assert args == ("/v1/detectors",)
    assert kwargs["json"]["name"] == "Inspector"
    assert kwargs["json"]["mode"] == "BINARY"
    assert kwargs["json"]["metadata"] == "{\"team\": \"qa\"}"
    assert detector.id == "det-123"


def test_list_detectors_returns_paginated_list() -> None:
    client = _make_client()
    client._http.get_json.return_value = {
        "count": 2,
        "next": None,
        "previous": None,
        "results": [
            {"id": "det-1", "name": "A", "query": "foo", "mode": "BINARY"},
            {"id": "det-2", "name": "B", "query": "bar", "mode": "BINARY"},
        ],
    }

    detectors = client.list_detectors()

    assert isinstance(detectors, PaginatedDetectorList)
    assert [d.id for d in detectors.results] == ["det-1", "det-2"]


def test_submit_image_query_includes_optional_fields() -> None:
    client = _make_client()
    client._http.post_json.return_value = {"id": "iq-1", "status": "PENDING", "detector_id": "det-1"}

    result = client.submit_image_query(
        detector="det-1",
        image=_sample_jpeg_bytes(),
        wait=0.0,
        patience_time=45.0,
        confidence_threshold=0.9,
        human_review="ALWAYS",
        metadata={"source": "field"},
        inspection_id="insp-7",
        image_query_id="iq-custom",
        want_async=True,
        request_timeout=60.0,
    )

    assert isinstance(result, ImageQuery)
    call = client._http.post_json.call_args
    form = call.kwargs["data"]
    assert form["wait"] == 0.0
    assert form["patience_time"] == 45.0
    assert form["confidence_threshold"] == 0.9
    assert form["human_review"] == "ALWAYS"
    assert form["metadata"] == "{\"source\": \"field\"}"
    assert form["inspection_id"] == "insp-7"
    assert form["image_query_id"] == "iq-custom"
    assert form["want_async"] == "true"


def test_submit_image_query_json_payload() -> None:
    client = _make_client()
    client._http.post_json.return_value = {"id": "iq-456", "status": "PENDING", "detector_id": "det-2"}
    encoded = base64.b64encode(b"jpeg").decode()

    client.submit_image_query_json(
        detector="det-2",
        image=encoded,
        wait=1.5,
        confidence_threshold=0.75,
        patience_time=20.0,
        human_review="DEFAULT",
        inspection_id="insp-9",
    )

    call = client._http.post_json.call_args
    payload = call.kwargs["json"]
    assert payload["detector_id"] == "det-2"
    assert payload["wait"] == 1.5
    assert payload["confidence_threshold"] == 0.75
    assert payload["patience_time"] == 20.0
    assert payload["human_review"] == "DEFAULT"


def test_submit_image_query_defaults_match_docs() -> None:
    client = _make_client()
    client._http.post_json.return_value = {"id": "iq-default", "status": "PENDING", "detector_id": "det-1"}

    client.submit_image_query(detector="det-1", image=_sample_jpeg_bytes())

    form = client._http.post_json.call_args.kwargs["data"]
    assert form["wait"] == 30.0
    assert "patience_time" not in form


def test_get_result_normalizes_payload() -> None:
    client = _make_client()
    client._http.get_json.return_value = {
        "id": "iq-789",
        "status": "PROCESSING",
        "detector_id": "det-1",
        "result_type": "BINARY",
        "result": {"label": "NO", "confidence": 0.55, "count": 2},
    }

    result = client.get_result("iq-789")

    assert isinstance(result, QueryResult)
    assert result.label == "NO"
    assert result.confidence == 0.55
    assert result.extra == {"count": 2, "detector_id": "det-1"}


def test_add_label_serializes_rois() -> None:
    client = _make_client()
    roi = ROI(label="door", top_left=(0.1, 0.2), bottom_right=(0.3, 0.4))

    client.add_label("iq-1", "YES", rois=[roi])

    call = client._http.post_json.call_args
    payload = call.kwargs["json"]
    assert payload["image_query_id"] == "iq-1"
    assert payload["label"] == "YES"
    assert payload["rois"][0]["label"] == "door"


def test_wait_for_confident_result_uses_nested_confidence(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client()
    responses = [
        {"id": "iq", "status": "PROCESSING", "result": {"confidence": 0.5}},
        {"id": "iq", "status": "DONE", "result": {"confidence": 0.95}},
    ]
    client._http.get_json.side_effect = responses

    result = client.wait_for_confident_result("iq", confidence_threshold=0.9, timeout_sec=5, poll_interval=0)

    assert isinstance(result, ImageQuery)
    assert result.result.confidence == 0.95  # type: ignore[union-attr]


def test_ask_ml_uses_documented_wait_default() -> None:
    client = _make_client()
    expected = ImageQuery(id="iq-ml")
    client.submit_image_query = Mock(return_value=expected)

    result = client.ask_ml("det-1", b"jpeg")

    assert result is expected
    kwargs = client.submit_image_query.call_args.kwargs
    assert kwargs["wait"] == 30.0


def test_ask_confident_defaults_to_documented_wait() -> None:
    client = _make_client()
    query = ImageQuery(id="iq-conf")
    client.submit_image_query = Mock(return_value=query)
    client.wait_for_confident_result = Mock(return_value=query)

    result = client.ask_confident("det-1", b"jpeg")

    assert result is query
    submit_kwargs = client.submit_image_query.call_args.kwargs
    assert submit_kwargs["wait"] == 30.0
    wait_kwargs = client.wait_for_confident_result.call_args.kwargs
    assert wait_kwargs["timeout_sec"] == 30.0


def test_async_submit_image_query_returns_image_query() -> None:
    async def run() -> None:
        client, http = _make_async_client()
        http.post_json.return_value = {"id": "iq-async", "status": "PENDING"}

        result = await client.submit_image_query(detector="det-async")

        assert isinstance(result, ImageQuery)
        http.post_json.assert_awaited_once()

    asyncio.run(run())


def test_async_list_image_queries_returns_paginated() -> None:
    async def run() -> None:
        client, http = _make_async_client()
        http.get_json.return_value = {
            "count": 1,
            "next": None,
            "previous": None,
            "results": [{"id": "iq-1", "status": "DONE", "detector_id": "det-1"}],
        }

        listing = await client.list_image_queries()

        assert isinstance(listing, PaginatedImageQueryList)
        assert [iq.id for iq in listing.results] == ["iq-1"]

    asyncio.run(run())


def test_experimental_create_bounding_box_detector_uses_helper() -> None:
    client = _make_client()
    api = ExperimentalApi(sync_client=client)
    client._http.post_json.return_value = {
        "id": "det",
        "name": "bbox",
        "query": "Locate",
        "mode": "BOUNDING_BOX",
    }

    detector = api.create_bounding_box_detector("bbox", "Locate", "person", max_num_bboxes=3)

    assert isinstance(detector, Detector)
    call = client._http.post_json.call_args
    payload = call.kwargs["json"]
    assert payload["mode"] == "BOUNDING_BOX"
    assert payload["mode_configuration"]["class_name"] == "person"


def test_experimental_create_rule_matches_documentation() -> None:
    client = _make_client()
    api = ExperimentalApi(sync_client=client)
    client._http.post_json.return_value = {
        "id": 42,
        "detector_id": "det-1",
        "detector_name": "Door Detector",
        "name": "Door Open Alert",
        "enabled": True,
        "snooze_time_enabled": False,
        "snooze_time_value": 1800,
        "snooze_time_unit": "SECONDS",
        "human_review_required": False,
        "condition": {"verb": "CHANGED_TO", "parameters": {"label": "YES"}},
        "action": {"channel": "EMAIL", "recipient": "alerts@example.com", "include_image": True},
        "webhook_action": None,
    }

    rule = api.create_rule(
        detector="det-1",
        rule_name="Door Open Alert",
        channel=ChannelEnum.EMAIL,
        recipient="alerts@example.com",
        alert_on="CHANGED_TO",
        include_image=True,
        condition_parameters={"label": "YES"},
        snooze_time_value=1800,
    )

    call = client._http.post_json.call_args
    assert call.args[0] == "/v1/detectors/det-1/alerts"
    payload = call.kwargs["json"]
    assert payload["name"] == "Door Open Alert"
    assert payload["condition"]["verb"] == "CHANGED_TO"
    assert payload["actions"][0]["channel"] == "EMAIL"
    assert payload["actions"][0]["include_image"] is True
    assert payload["snooze_time_value"] == 1800
    assert rule.name == "Door Open Alert"
    assert rule.action is not None


def test_experimental_delete_all_rules_without_detector() -> None:
    client = _make_client()
    api = ExperimentalApi(sync_client=client)
    client._http.delete.return_value = {"deleted": 3}

    deleted = api.delete_all_rules()

    client._http.delete.assert_called_once_with("/v1/rules", params=None)
    assert deleted == 3


def test_make_generic_api_request_accepts_files() -> None:
    client = _make_client()
    api = ExperimentalApi(sync_client=client)
    response = Mock()
    response.status_code = 200
    response.headers = {"Content-Type": "application/json"}
    response.json = Mock(return_value={"ok": True})
    client._http.request_raw.return_value = response

    result = api.make_generic_api_request(
        endpoint="/v1/detectors", method="post", files={"image": ("photo.jpg", b"data", "image/jpeg")}
    )

    client._http.request_raw.assert_called_once()
    kwargs = client._http.request_raw.call_args.kwargs
    assert "files" in kwargs
    assert kwargs["files"]["image"][0] == "photo.jpg"
    assert result.body == {"ok": True}

