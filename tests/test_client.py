import json
import time

import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import Answer, AnswerLabel


@pytest.fixture
def client():
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")
    yield client
    client.close()


def test_init_requires_api_token():
    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://api.example.com")


def test_create_detector_uses_payload(monkeypatch, client):
    captured = {}
    response = {
        "id": "det-123",
        "name": "Widget",
        "mode": "binary",
        "query_text": "Is there a widget?",
        "threshold": 0.8,
        "status": "active",
    }

    def fake_post(path, **kwargs):
        captured["path"] = path
        captured["json"] = kwargs["json"]
        return response

    monkeypatch.setattr(client._http, "post_json", fake_post)

    detector = client.create_detector(name="Widget", mode="binary", query_text="Is there a widget?", threshold=0.8)

    assert captured["path"] == "/v1/detectors"
    assert captured["json"]["name"] == "Widget"
    assert captured["json"]["threshold"] == 0.8
    assert detector.id == "det-123"
    assert detector.mode.value == "binary"


def test_list_detectors_handles_items_wrapper(monkeypatch, client):
    payload = {
        "items": [
            {
                "id": "det-1",
                "name": "Demo",
                "mode": "binary",
                "query_text": "Is it there?",
                "threshold": 0.75,
                "status": "active",
            }
        ]
    }

    monkeypatch.setattr(client._http, "get_json", lambda path: payload)

    detectors = client.list_detectors()

    assert len(detectors) == 1
    assert detectors[0].id == "det-1"


def test_get_answer_returns_model(monkeypatch, client):
    answer_payload = {
        "image_query_id": "iq-1",
        "answer": "YES",
        "confidence": 0.42,
        "latency_ms": 123,
    }
    monkeypatch.setattr(client._http, "get_json", lambda path: answer_payload)

    answer = client.get_answer("iq-1")

    assert isinstance(answer, Answer)
    assert answer.answer is AnswerLabel.YES


def test_ask_image_posts_multipart(monkeypatch, client, tmp_path):
    img_path = tmp_path / "sample.jpg"
    img_path.write_bytes(b"fake-bytes")

    captured = {}
    answer_payload = {
        "image_query_id": "iq-123",
        "answer": "NO",
        "confidence": 0.5,
    }

    def fake_post(path, **kwargs):
        captured.update(kwargs)
        return answer_payload

    monkeypatch.setattr(client._http, "post_json", fake_post)

    answer = client.ask_image(
        "det-123",
        image=img_path,
        wait=True,
        confidence_threshold=0.9,
        metadata={"source": "unit-test"},
        inspection_id="insp-7",
    )

    assert captured["data"]["detector_id"] == "det-123"
    assert captured["data"]["wait"] == "true"
    assert json.loads(captured["data"]["metadata"]) == {"source": "unit-test"}
    assert captured["files"]["image"][1] == b"fake-bytes"
    assert isinstance(answer, Answer)


def test_ask_ml_posts_json(monkeypatch, client):
    captured = {}
    answer_payload = {
        "image_query_id": "iq-json",
        "answer": "YES",
        "confidence": 0.33,
    }

    def fake_post(path, **kwargs):
        captured.update(kwargs)
        return answer_payload

    monkeypatch.setattr(client._http, "post_json", fake_post)

    answer = client.ask_ml("det-1", image="https://example.com/image.jpg", wait=True)

    assert captured["json"]["detector_id"] == "det-1"
    assert captured["json"]["wait"] is True
    assert answer.image_query_id == "iq-json"


def test_ask_confident_short_circuits(monkeypatch, client):
    confident_answer = Answer.parse({
        "image_query_id": "iq-1",
        "answer": "YES",
        "confidence": 0.95,
    })
    wait_called = False

    monkeypatch.setattr(client, "ask_image", lambda *args, **kwargs: confident_answer)

    def fake_wait(*args, **kwargs):
        nonlocal wait_called
        wait_called = True
        return confident_answer

    monkeypatch.setattr(client, "wait_for_confident_result", fake_wait)

    result = client.ask_confident("det-1", image=b"data", confidence_threshold=0.9)

    assert result is confident_answer
    assert wait_called is False


def test_ask_confident_waits_when_needed(monkeypatch, client):
    low = Answer.parse({
        "image_query_id": "iq-1",
        "answer": "YES",
        "confidence": 0.2,
    })
    high = Answer.parse({
        "image_query_id": "iq-1",
        "answer": "YES",
        "confidence": 0.91,
    })
    wait_args = {}

    monkeypatch.setattr(client, "ask_image", lambda *args, **kwargs: low)

    def fake_wait(answer, **kwargs):
        wait_args.update(kwargs)
        return high

    monkeypatch.setattr(client, "wait_for_confident_result", fake_wait)

    result = client.ask_confident("det-1", image=b"data", confidence_threshold=0.9, timeout_sec=10.0, poll_interval=0.1)

    assert result is high
    assert wait_args == {"confidence_threshold": 0.9, "timeout_sec": 10.0, "poll_interval": 0.1}


def test_wait_for_confident_result_polls(monkeypatch, client):
    answers = [
        Answer.parse({"image_query_id": "iq-1", "answer": "NO", "confidence": 0.2}),
        Answer.parse({"image_query_id": "iq-1", "answer": "NO", "confidence": 0.92}),
    ]

    def fake_get_answer(_):
        return answers.pop(0)

    monkeypatch.setattr(client, "get_answer", fake_get_answer)
    monkeypatch.setattr(time, "sleep", lambda _: None)

    result = client.wait_for_confident_result("iq-1", confidence_threshold=0.9, poll_interval=0)

    assert pytest.approx(result.confidence) == 0.92


def test_send_feedback_posts_json(monkeypatch, client):
    captured = {}

    def fake_post(path, **kwargs):
        captured.update(kwargs)
        return {"ok": True}

    monkeypatch.setattr(client._http, "post_json", fake_post)

    resp = client.send_feedback(image_query_id="iq-9", correct_label="YES", bboxes=[{"x": 1}])

    assert captured["json"]["correct_label"] == "YES"
    assert resp == {"ok": True}


def test_whoami_returns_identity(monkeypatch, client):
    payload = {"id": "user-1", "email": "user@example.com"}
    monkeypatch.setattr(client._http, "get_json", lambda path: payload)

    identity = client.whoami()

    assert identity == payload
