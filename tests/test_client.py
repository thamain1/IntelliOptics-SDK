from __future__ import annotations

import base64
import asyncio
from pathlib import Path
from typing import Any, Dict
from unittest.mock import AsyncMock, Mock

import pytest

from intellioptics import AsyncIntelliOptics, ExperimentalApi
from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError, ExperimentalFeatureUnavailable
from intellioptics.models import (
    Action,
    Condition,
    Detector,
    FeedbackIn,
    ImageQuery,
    QueryResult,
    Rule,
    UserIdentity,
)

from intellioptics.models import Detector, FeedbackIn, ImageQuery, QueryResult, UserIdentity



def test_init_requires_api_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)

    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://api.example.com")


def test_init_uses_environment_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "env-token")

    client = IntelliOptics()

    assert client._http.base == "https://example.invalid"  # type: ignore[attr-defined]
    assert client._http.headers["Authorization"] == "Bearer env-token"  # type: ignore[index]


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
    client._http = http  # type: ignore[attr-defined]
    client.experimental = ExperimentalApi(async_client=client)
    return client, http


def test_create_detector_builds_payload() -> None:
    client = _make_client()
    response = {
        "id": "det-123",
        "name": "Inspector",
        "mode": "binary",
        "query_text": "Is it OK?",
        "threshold": 0.8,
        "status": "active",
    }
    client._http.post_json.return_value = response

    detector = client.create_detector("Inspector", mode="binary", query_text="Is it OK?", threshold=0.8)

    client._http.post_json.assert_called_once_with(
        "/v1/detectors",
        json={
            "name": "Inspector",
            "mode": "binary",
            "query_text": "Is it OK?",
            "threshold": 0.8,
        },
    )
    assert detector == Detector(**response)


def test_list_detectors_handles_items_key() -> None:
    client = _make_client()
    client._http.get_json.return_value = {
        "items": [
            {"id": "det-1", "name": "A"},
            {"id": "det-2", "name": "B"},
        ]
    }

    detectors = client.list_detectors()

    assert [d.id for d in detectors] == ["det-1", "det-2"]


def test_submit_image_query_form_fields() -> None:
    client = _make_client()
    client._http.post_json.return_value = {"id": "iq-123", "status": "PENDING", "detector_id": "det-1"}

    image_bytes = b"jpeg"
    result = client.submit_image_query(detector="det-1", image=image_bytes, wait=False)

    assert isinstance(result, ImageQuery)
    call = client._http.post_json.call_args
    assert call.args == ("/v1/image-queries",)
    assert call.kwargs["data"] == {"detector_id": "det-1", "wait": "false"}
    filename, payload, content_type = call.kwargs["files"]["image"]
    assert filename == "image.jpg"
    assert payload == image_bytes
    assert content_type == "image/jpeg"


def test_submit_image_query_serializes_optional_fields() -> None:
    client = _make_client()
    client._http.post_json.return_value = {"id": "iq-777", "status": "PENDING"}

    result = client.submit_image_query(
        detector="det-9",
        prompt="Check the weld",
        wait=2.5,
        confidence_threshold=0.85,
        metadata={"source": "field"},
        inspection_id="insp-42",
    )

    call = client._http.post_json.call_args
    form = call.kwargs["data"]
    assert form["prompt"] == "Check the weld"
    assert form["wait"] == 2.5
    assert form["confidence_threshold"] == 0.85
    assert form["inspection_id"] == "insp-42"
    assert form["metadata"] == "{\"source\": \"field\"}"
    assert result.id == "iq-777"


def test_submit_image_query_json_payload() -> None:
    client = _make_client()
    client._http.post_json.return_value = {"id": "iq-456", "status": "PENDING"}
    encoded = base64.b64encode(b"jpeg").decode()

    result = client.submit_image_query_json(detector="det-2", image=encoded, wait=True)

    call = client._http.post_json.call_args
    assert call.args == ("/v1/image-queries-json",)
    assert call.kwargs["json"] == {"detector_id": "det-2", "image": encoded, "wait": True}
    assert isinstance(result, ImageQuery)


def test_submit_image_query_normalizes_legacy_payload() -> None:
    client = _make_client()
    client._http.post_json.return_value = {
        "image_query_id": "iq-legacy",
        "answer": "YES",
        "confidence": 0.93,
        "latency_ms": 410,
        "model_version": "demo-v1",
    }

    query = client.submit_image_query(detector="det-legacy")

    assert query.id == "iq-legacy"
    assert query.status == "DONE"
    assert query.label == "YES"
    assert query.extra == {"latency_ms": 410, "model_version": "demo-v1"}


def test_get_result_normalizes_structured_payload() -> None:
    client = _make_client()
    client._http.get_json.return_value = {
        "id": "iq-789",
        "status": "PROCESSING",
        "detector_id": "det-1",
        "result_type": "binary",
        "result": {"label": "NO", "confidence": 0.55, "count": 2},
    }

    result = client.get_result("iq-789")

    assert isinstance(result, QueryResult)
    assert result.label == "NO"
    assert result.confidence == 0.55
    assert result.extra == {"count": 2}


def test_submit_feedback_accepts_kwargs() -> None:
    client = _make_client()
    client._http.post_json.return_value = {}

    response = client.submit_feedback(image_query_id="iq-1", correct_label="NO")

    client._http.post_json.assert_called_once_with(
        "/v1/feedback",
        json={"image_query_id": "iq-1", "correct_label": "NO"},
    )
    assert response == {}


def test_submit_feedback_accepts_model() -> None:
    client = _make_client()
    client._http.post_json.return_value = {"status": "ok"}
    feedback = FeedbackIn(image_query_id="iq-2", correct_label="YES")

    response = client.submit_feedback(feedback)

    client._http.post_json.assert_called_once()
    assert response == {"status": "ok"}


def test_submit_feedback_rejects_mixed_inputs() -> None:
    client = _make_client()

    with pytest.raises(ValueError):
        client.submit_feedback(FeedbackIn(image_query_id="iq", correct_label="YES"), correct_label="NO")


def test_wait_for_confident_result(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client()

    responses = [
        ImageQuery(id="iq", status="PROCESSING"),
        ImageQuery(id="iq", status="DONE", confidence=0.95),
    ]

    def fake_get_image_query(image_query_id: str) -> ImageQuery:
        return responses.pop(0)

    monkeypatch.setattr(client, "get_image_query", fake_get_image_query)
    monkeypatch.setattr("intellioptics.client.time.sleep", lambda _: None)

    result = client.wait_for_confident_result("iq", timeout_sec=5, poll_interval=0)

    assert isinstance(result, ImageQuery)
    assert result.status == "DONE"
    assert result.confidence == 0.95


def test_whoami_returns_identity(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client()
    identity_payload: Dict[str, Any] = {
        "id": "user-123",
        "email": "user@example.com",
        "name": "Example User",
        "tenant": "tenant-789",
        "roles": ["admin", "user"],
    }
    client._http.get_json.return_value = identity_payload

    identity = client.whoami()

    assert isinstance(identity, UserIdentity)
    serializer = getattr(identity, "model_dump", identity.dict)
    assert serializer() == identity_payload


def test_list_image_queries_returns_models() -> None:
    client = _make_client()
    client._http.get_json.return_value = {"items": [{"id": "iq-1", "status": "PENDING"}]}

    queries = client.list_image_queries()

    assert len(queries) == 1
    assert isinstance(queries[0], ImageQuery)


def test_ask_async_aliases_submit(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client()
    monkeypatch.setattr(client, "submit_image_query", Mock(return_value="ok"))

    result = client.ask_async("det-1", b"img")

    assert result == "ok"
    client.submit_image_query.assert_called_once()


def test_experimental_unknown_method_raises() -> None:
    client = _make_client()

    with pytest.raises(ExperimentalFeatureUnavailable):
        client.experimental.create_detector_group()  # type: ignore[attr-defined]


def test_experimental_create_alert_builds_payload() -> None:
    client = _make_client()
    condition = Condition(verb="CHANGED_TO", parameters={"label": "YES"})
    action = Action(channel="EMAIL", recipient="ops@example.com", include_image=True)
    serialize_condition = getattr(condition, "model_dump", condition.dict)
    serialize_action = getattr(action, "model_dump", action.dict)

    client._http.post_json.return_value = {
        "id": 1,
        "detector_id": "det-1",
        "detector_name": "Door",
        "name": "Door alert",
        "enabled": True,
        "snooze_time_enabled": False,
        "snooze_time_value": 3600,
        "snooze_time_unit": "SECONDS",
        "human_review_required": False,
        "condition": serialize_condition(),
        "action": serialize_action(),
        "webhook_action": None,
    }

    rule = client.experimental.create_alert(
        "det-1",
        "Door alert",
        condition,
        actions=[action],
    )

    assert isinstance(rule, Rule)
    call = client._http.post_json.call_args
    assert call.args == ("/v1/detectors/det-1/alerts",)
    payload = call.kwargs["json"]
    assert payload["name"] == "Door alert"
    assert payload["condition"]["verb"] == "CHANGED_TO"
    assert payload["actions"][0]["channel"] == "EMAIL"


def test_experimental_create_rule_parses_parameters() -> None:
    client = _make_client()
    client._http.post_json.return_value = {
        "id": 2,
        "detector_id": "det-9",
        "detector_name": "Detector",
        "name": "My rule",
        "enabled": True,
        "snooze_time_enabled": False,
        "snooze_time_value": 3600,
        "snooze_time_unit": "SECONDS",
        "human_review_required": False,
        "condition": {"verb": "CHANGED_TO", "parameters": {"label": "YES"}},
        "action": {"channel": "EMAIL", "recipient": "ops@example.com", "include_image": False},
        "webhook_action": None,
    }

    client.experimental.create_rule(
        "det-9",
        "My rule",
        "email",
        "ops@example.com",
        condition_parameters='{"label": "YES"}',
    )

    payload = client._http.post_json.call_args.kwargs["json"]
    assert payload["condition"]["parameters"]["label"] == "YES"
    assert payload["actions"][0]["channel"] == "EMAIL"


def test_experimental_create_note_attaches_image(monkeypatch: pytest.MonkeyPatch) -> None:
    client = _make_client()
    monkeypatch.setattr("intellioptics.client.to_jpeg_bytes", lambda _: b"img-bytes")

    client.experimental.create_note("det-1", "Review this", image=b"raw")

    call = client._http.post_json.call_args
    assert call.args == ("/v1/detectors/det-1/notes",)
    files = call.kwargs["files"]
    assert files["image"][0] == "note.jpg"
    assert files["image"][1] == b"img-bytes"
    assert call.kwargs["data"] == {"note": "Review this"}


def test_experimental_delete_all_rules_returns_count() -> None:
    client = _make_client()
    client._http.delete.return_value = {"deleted": 5}

    assert client.experimental.delete_all_rules("det-1") == 5
    client._http.delete.assert_called_once_with("/v1/rules", params={"detector_id": "det-1"})


def test_experimental_make_generic_api_request_parses_json() -> None:
    client = _make_client()
    response = Mock()
    response.status_code = 202
    response.headers = {"Content-Type": "application/json"}
    response.json.return_value = {"ok": True}
    client._http.request_raw.return_value = response

    result = client.experimental.make_generic_api_request(
        endpoint="/v1/ping", method="post", body={"hello": "world"}
    )

    assert result.status_code == 202
    assert result.body == {"ok": True}
    client._http.request_raw.assert_called_once_with(
        "POST", "/v1/ping", headers=None, json={"hello": "world"}
    )


def test_experimental_download_mlbinary_writes_file(tmp_path: Path) -> None:
    client = _make_client()
    response = Mock()
    response.content = b"binary-data"
    response.headers = {"Content-Type": "application/octet-stream", "Content-Disposition": 'attachment; filename="model.bin"'}
    client._http.request_raw.return_value = response

    output_dir = tmp_path / "mlbinary"
    client.experimental.download_mlbinary("det-5", str(output_dir))

    saved = output_dir.joinpath("model.bin")
    assert saved.exists()
    assert saved.read_bytes() == b"binary-data"


def test_async_submit_image_query_uses_async_http() -> None:
    async def run() -> None:
        client, http = _make_async_client()
        http.post_json.return_value = {"id": "iq-async", "status": "PENDING"}

        result = await client.submit_image_query(detector="det-async")

        assert isinstance(result, ImageQuery)
        http.post_json.assert_awaited_once()

    asyncio.run(run())


def test_async_list_image_queries_handles_items() -> None:
    async def run() -> None:
        client, http = _make_async_client()
        http.get_json.return_value = {"items": [{"id": "iq-1", "status": "DONE"}]}

        items = await client.list_image_queries()

        assert [iq.id for iq in items] == ["iq-1"]
        http.get_json.assert_awaited_once()

    asyncio.run(run())
