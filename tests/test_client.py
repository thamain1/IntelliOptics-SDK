import json
import pytest
from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import UserIdentity, FeedbackIn
from intellioptics.models import UserIdentity, Detector, ImageQuery
from intellioptics.models import Detector, UserIdentity


def test_init_requires_api_token(monkeypatch):
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)

    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://example.com")


def test_init_uses_environment(monkeypatch):
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "env-token")
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://example.com")

    client = IntelliOptics()

    assert client._http.headers["Authorization"] == "Bearer env-token"
from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError


def test_init_requires_api_token(monkeypatch):
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)

    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://example.com")


def test_init_uses_environment(monkeypatch):
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "env-token")
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://example.com")

    client = IntelliOptics()

    assert client._http.headers["Authorization"] == "Bearer env-token"
from intellioptics.client import IntelliOptics
from intellioptics.models import Detector


class StubHttpClient:
    def __init__(self, response):
        self._response = response
        self.last_request = None

    def post_json(self, path, json=None, **kwargs):
        self.last_request = {"path": path, "json": json, "kwargs": kwargs}
        return self._response

import base64
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intellioptics.client import IntelliOptics
from intellioptics.models import ImageQuery


@pytest.fixture()
def client():
    return IntelliOptics(endpoint="https://api.example.com", api_token="token")


def test_submit_image_query_form_fields(client):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "id": "iq_123",
        "detector_id": "det-1",
        "status": "PENDING",
    }

    image_bytes = b"fake-jpeg"

    with patch("intellioptics._http.requests.post", return_value=mock_response) as mock_post:
        result = client.submit_image_query(detector="det-1", image=image_bytes, wait=False)

    assert isinstance(result, ImageQuery)
    assert result.id == "iq_123"

    assert mock_post.call_args.kwargs["data"] == {"detector_id": "det-1", "wait": "false"}

    files = mock_post.call_args.kwargs["files"]
    assert "image" in files
    filename, payload, content_type = files["image"]
    assert filename == "image.jpg"
    assert payload == image_bytes
    assert content_type == "image/jpeg"


def test_submit_image_query_json_payload(client):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "id": "iq_456",
        "detector_id": "det-2",
        "status": "PENDING",
    }

    image_payload = base64.b64encode(b"jpeg").decode()

    with patch("intellioptics._http.requests.post", return_value=mock_response) as mock_post:
        result = client.submit_image_query_json(detector="det-2", image=image_payload, wait=True)

    assert isinstance(result, ImageQuery)
    assert result.id == "iq_456"

    assert mock_post.call_args.kwargs["json"] == {
        "detector_id": "det-2",
        "image": image_payload,
        "wait": True,
    }
    assert "files" not in mock_post.call_args.kwargs
from pathlib import Path
from unittest.mock import Mock

import pytest

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from intellioptics.client import IntelliOptics
from intellioptics.models import FeedbackIn


@pytest.fixture
def client():
    def _make(response):
        sdk = IntelliOptics(endpoint="https://example.com", api_token="token")
        sdk._http = StubHttpClient(response)
        return sdk

    return _make


def test_create_detector_builds_payload_and_hydrates_response(client):
    response = {
        "id": "det-123",
        "name": "An inspector",
        "mode": "binary",
        "query_text": "Is this defective?",
        "threshold": 0.9,
        "status": "active",
    }
    sdk = client(response)

    detector = sdk.create_detector(
        name="An inspector",
        mode="binary",
        query_text="Is this defective?",
        threshold=0.9,
    )

    assert sdk._http.last_request == {
        "path": "/v1/detectors",
        "json": {
            "name": "An inspector",
            "mode": "binary",
            "query_text": "Is this defective?",
            "threshold": 0.9,
        },
        "kwargs": {},
    }
    assert detector == Detector(**response)


def test_create_detector_omits_threshold_when_not_provided(client):
    response = {
        "id": "det-456",
        "name": "Counting bot",
        "mode": "count",
        "query_text": "How many widgets?",
        "threshold": 0.75,
        "status": "active",
    }
    sdk = client(response)

    detector = sdk.create_detector(
        name="Counting bot",
        mode="count",
        query_text="How many widgets?",
    )

    assert sdk._http.last_request == {
        "path": "/v1/detectors",
        "json": {
            "name": "Counting bot",
            "mode": "count",
            "query_text": "How many widgets?",
        },
        "kwargs": {},
    }
    assert detector == Detector(**response)
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")
    client._http = Mock()
    return client


def test_submit_feedback_posts_payload(client):
    feedback = FeedbackIn(
        image_query_id="iq-123",
        correct_label="YES",
        bboxes=[{"x": 1, "y": 2, "w": 3, "h": 4}],
    )
    client._http.post_json.return_value = {"status": "ok"}

    response = client.submit_feedback(feedback)

    client._http.post_json.assert_called_once_with(
        "/v1/feedback",
        json={
            "image_query_id": "iq-123",
            "correct_label": "YES",
            "bboxes": [{"x": 1, "y": 2, "w": 3, "h": 4}],
        },
    )
    assert response == {"status": "ok"}


def test_submit_feedback_with_kwargs_and_empty_response(client):
    client._http.post_json.return_value = {}

    response = client.submit_feedback(image_query_id="iq-456", correct_label="NO")

    client._http.post_json.assert_called_once_with(
        "/v1/feedback",
        json={"image_query_id": "iq-456", "correct_label": "NO"},
    )
    assert response == {}

from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import Detector, UserIdentity
from intellioptics.models import ImageQuery, QueryResult, UserIdentity


def test_init_requires_api_token():
    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://api.example.com")


def test_whoami_returns_user_identity(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    identity_payload = {
        "id": "user-123",
        "email": "user@example.com",
        "name": "Example User",
        "tenant": "tenant-789",
        "roles": ["admin", "user"],
    }
    requested_path = {}

    def fake_get_json(path):
        requested_path["value"] = path
        return identity_payload

    monkeypatch.setattr(client._http, "get_json", fake_get_json)

    identity = client.whoami()


def test_init_uses_environment_defaults(monkeypatch):
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://example.invalid")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "env-token")

    client = IntelliOptics()

    assert client._http.base == "https://example.invalid"
    assert client._http.headers["Authorization"] == "Bearer env-token"
    assert requested_path["value"] == "/v1/users/me"
    assert isinstance(identity, UserIdentity)
    serializer = getattr(identity, "model_dump", identity.dict)
    assert serializer() == identity_payload


def test_submit_image_query_forwards_metadata(monkeypatch):
  
def _image_query_response():
    return {"id": "iq-123", "status": "PENDING"}


def test_submit_image_query_forwards_dict_metadata(monkeypatch):

def test_submit_image_query_forwards_metadata_dict(monkeypatch):

def test_create_detector_serializes_labels(monkeypatch):

def test_submit_image_query_normalizes_legacy_payload(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    legacy_payload = {
        "image_query_id": "iq-123",
        "answer": "YES",
        "confidence": 0.87,
    }

    def fake_post_json(path, **kw):
        assert path == "/v1/image-queries"
        return legacy_payload

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    iq = client.submit_image_query(detector="det-1")

    assert isinstance(iq, ImageQuery)
    assert iq.id == "iq-123"
    assert iq.label == "YES"
    assert iq.status == "DONE"


def test_get_result_returns_query_result(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    legacy_payload = {
        "image_query_id": "iq-456",
        "answer": "NO",
        "confidence": 0.12,
    }

    def fake_get_json(path, **kw):
        assert path == "/v1/image-queries/iq-456"
        return legacy_payload

    monkeypatch.setattr(client._http, "get_json", fake_get_json)

    result = client.get_result("iq-456")

    assert isinstance(result, QueryResult)
    assert result.id == "iq-456"
    assert result.label == "NO"
    assert result.status == "DONE"
def test_submit_image_query_encodes_optional_fields(monkeypatch):

def test_submit_image_query_forwards_metadata(monkeypatch):

    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    captured = {}

    def fake_post_json(path, *, files=None, data=None):
        captured["path"] = path
        captured["files"] = files
        captured["data"] = data
        return _image_query_response()

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    metadata = {"operator": "alice", "shift": 2}
    iq = client.submit_image_query(detector="det-123", metadata=metadata)

    assert captured["path"] == "/v1/image-queries"
    assert captured["files"] is None
    assert captured["data"]["detector_id"] == "det-123"
    assert captured["data"]["metadata"] == json.dumps(metadata)
    assert iq.id == "iq-123"


def test_submit_image_query_forwards_non_dict_metadata(monkeypatch):

    def fake_post_json(path, files=None, data=None):
        captured["path"] = path
        captured["files"] = files
        captured["data"] = data
        return {"id": "iq-1", "status": "PENDING"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    metadata = {"key": "value", "count": 3}

    result = client.submit_image_query(detector="det-1", metadata=metadata)

    assert result.id == "iq-1"
    assert captured["path"] == "/v1/image-queries"
    assert captured["files"] is None
    assert "metadata" in captured["data"]
    assert json.loads(captured["data"]["metadata"]) == metadata


def test_submit_image_query_preserves_non_dict_metadata(monkeypatch):

    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    captured = {}

    def fake_post_json(path, *, files=None, data=None, **kwargs):

    def fake_post_json(path, *, files=None, data=None):
        captured["data"] = data
        return _image_query_response()

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    iq = client.submit_image_query(metadata="plain-text")

    assert captured["data"]["metadata"] == "plain-text"
    assert iq.id == "iq-123"

    def fake_post_json(path, files=None, data=None):
        captured["data"] = data
        return {"id": "iq-1", "status": "PENDING"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    metadata = "custom string"

    client.submit_image_query(detector="det-1", metadata=metadata)

    assert captured["data"]["metadata"] == metadata

    def fake_post_json(path, json, **kwargs):
        captured["path"] = path
        captured["json"] = json
        return {"id": "det-123", "name": json["name"], "labels": json.get("labels", [])}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    detector = client.create_detector("demo", labels=["yes", "no"])

    assert captured["path"] == "/v1/detectors"
    assert captured["json"] == {"name": "demo", "labels": ["yes", "no"]}
    assert isinstance(detector, Detector)
    assert detector.labels == ["yes", "no"]


def test_list_detectors_handles_items_envelope(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    payload = {
        "items": [
            {"id": "det-1", "name": "alpha", "labels": ["one"]},
            {"id": "det-2", "name": "beta", "labels": []},
        ]
    }

    monkeypatch.setattr(client._http, "get_json", lambda path: payload if path == "/v1/detectors" else {})

    detectors = client.list_detectors()

    assert all(isinstance(d, Detector) for d in detectors)
    assert [d.id for d in detectors] == ["det-1", "det-2"]
    assert detectors[0].labels == ["one"]


def test_get_detector_deserializes_labels(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    def fake_get_json(path):
        assert path == "/v1/detectors/det-42"
        return {"id": "det-42", "name": "gamma", "labels": ["ok"]}

    monkeypatch.setattr(client._http, "get_json", fake_get_json)

    detector = client.get_detector("det-42")

    assert isinstance(detector, Detector)
    assert detector.labels == ["ok"]

    def fake_post_json(path, *, files=None, data=None, **_):
        captured["path"] = path
        captured["files"] = files
        captured["data"] = data
        return {"id": "iq-123", "status": "PENDING"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    metadata = {"source": "sdk", "tags": ["demo"]}

    iq = client.submit_image_query(
        detector="det_123",
        image=b"fake-bytes",
        prompt="Describe the scene",
        wait=2.5,
        confidence_threshold=0.8,
        metadata=metadata,
        inspection_id="insp-456",
    )

    assert captured["path"] == "/v1/image-queries"
    assert "image" in captured["files"]
    assert captured["files"]["image"][0] == "image.jpg"

    form = captured["data"]
    assert form["detector_id"] == "det_123"
    assert form["prompt"] == "Describe the scene"
    assert form["wait"] == 2.5
    assert form["confidence_threshold"] == 0.8
    assert form["inspection_id"] == "insp-456"
    assert json.loads(form["metadata"]) == metadata
    assert iq.id == "iq-123"

    def fake_post_json(path, *, files=None, data=None):
        captured["path"] = path
        captured["files"] = files
        captured["data"] = data
        return {"id": "iq-123"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    metadata = {"foo": "bar"}

    image_query = client.submit_image_query(detector="det-456", metadata=metadata)

    assert captured["path"] == "/v1/image-queries"
    assert captured["files"] is None
    assert json.loads(captured["data"]["metadata"]) == metadata
    assert image_query.id == "iq-123"

    metadata = {"foo": "bar", "nested": {"answer": 42}}

    iq = client.submit_image_query(detector="det-1", metadata=metadata)

    assert iq.id == "iq-123"
    assert captured["path"] == "/v1/image-queries"
    assert captured["files"] is None
    assert json.loads(captured["data"]["metadata"]) == metadata

def test_submit_feedback_posts_feedback_payload(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    payload_capture = {}

    def fake_post_json(path, *, json):
        payload_capture["path"] = path
        payload_capture["json"] = json
        return {"status": "ok"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    result = client.submit_feedback(
        image_query_id="iq-123",
        correct_label="YES",
        bboxes=[{"x": 1, "y": 2, "width": 3, "height": 4}],
    )

    assert payload_capture["path"] == "/v1/feedback"
    assert payload_capture["json"] == {
        "image_query_id": "iq-123",
        "correct_label": "YES",
        "bboxes": [{"x": 1, "y": 2, "width": 3, "height": 4}],
    }
    assert result == {"status": "ok"}


def test_submit_feedback_handles_empty_response(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    def fake_post_json(path, *, json):
        assert path == "/v1/feedback"
        assert json == {"image_query_id": "iq-456", "correct_label": "NO"}
        raise ValueError("No JSON object could be decoded")

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    feedback = FeedbackIn(image_query_id="iq-456", correct_label="NO")

    assert client.submit_feedback(feedback) == {}
def test_submit_image_query_builds_multipart_form(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    detector = Detector(id="det-123", name="Demo", labels=[])
    image_bytes = b'\xff\xd8fakejpeg'
    captured = {}

    def fake_post_json(path, **kwargs):
        captured["path"] = path
        captured["files"] = kwargs.get("files")
        captured["data"] = kwargs.get("data")
        return {"id": "iq-123", "detector_id": detector.id, "status": "PENDING"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    result = client.submit_image_query(detector=detector, image=image_bytes, wait=False)

    assert captured["path"] == "/v1/image-queries"
    assert captured["data"] == {"detector_id": detector.id, "wait": "false"}
    assert "image" in captured["files"]
    filename, payload, mimetype = captured["files"]["image"]
    assert filename == "image.jpg"
    assert payload == image_bytes
    assert mimetype == "image/jpeg"
    assert isinstance(result, ImageQuery)
    assert result.id == "iq-123"


def test_submit_image_query_omits_optional_fields(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    captured = {}

    def fake_post_json(path, **kwargs):
        captured["path"] = path
        captured["files"] = kwargs.get("files")
        captured["data"] = kwargs.get("data")
        return {"id": "iq-456", "detector_id": "det-456", "status": "PENDING"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    result = client.submit_image_query(detector="det-456")

    assert captured["path"] == "/v1/image-queries"
    assert captured["data"] == {"detector_id": "det-456"}
    assert captured["files"] is None
    assert isinstance(result, ImageQuery)
    assert result.id == "iq-456"


def test_submit_image_query_json_payload(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    captured = {}

    def fake_post_json(path, **kwargs):
        captured["path"] = path
        captured["json"] = kwargs.get("json")
        return {"id": "iq-json", "detector_id": "det-789", "status": "PENDING"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    image_payload = "YmFzZTY0"
    result = client.submit_image_query_json(detector="det-789", image_base64=image_payload, wait=True)

    assert captured["path"] == "/v1/image-queries-json"
    assert captured["json"] == {"detector_id": "det-789", "image": image_payload, "wait": True}
    assert isinstance(result, ImageQuery)
    assert result.id == "iq-json"
def test_create_detector_sends_expected_payload_and_parses_response(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    posted = {}

    def fake_post_json(path, json=None, **kwargs):
        posted["path"] = path
        posted["json"] = json
        return {
            "id": "det-123",
            "name": json["name"],
            "mode": json["mode"],
            "query_text": json["query_text"],
            "threshold": json.get("threshold", 0.75),
            "status": "active",
        }

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    detector = client.create_detector(
        name="Example Detector",
        mode="binary",
        query_text="Does the image contain a cat?",
        threshold=0.88,
    )

    assert posted["path"] == "/v1/detectors"
    assert posted["json"] == {
        "name": "Example Detector",
        "mode": "binary",
        "query_text": "Does the image contain a cat?",
        "threshold": 0.88,
    }
    assert isinstance(detector, Detector)
    assert detector.id == "det-123"
    assert detector.name == "Example Detector"
    assert detector.mode == "binary"
    assert detector.query_text == "Does the image contain a cat?"
    assert detector.threshold == 0.88
    assert detector.status == "active"


def test_create_detector_omits_threshold_when_none(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    posted = {}

    def fake_post_json(path, json=None, **kwargs):
        posted["json"] = json
        return {
            "id": "det-456",
            "name": json["name"],
            "mode": json["mode"],
            "query_text": json["query_text"],
            "threshold": 0.75,
            "status": "active",
        }

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    detector = client.create_detector(
        name="Thresholdless",
        mode="custom",
        query_text="Look for anomalies",
        threshold=None,
    )

    assert posted["json"] == {
        "name": "Thresholdless",
        "mode": "custom",
        "query_text": "Look for anomalies",
    }
    assert detector.threshold == 0.75


def test_list_detectors_parses_items(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    payload = {
        "items": [
            {
                "id": "det-1",
                "name": "First",
                "mode": "binary",
                "query_text": "Is there a scratch?",
                "threshold": 0.9,
                "status": "active",
            },
            {
                "id": "det-2",
                "name": "Second",
                "mode": "count",
                "query_text": "How many defects?",
                "threshold": 0.5,
                "status": "training",
            },
        ]
    }

    requested_path = {}

    def fake_get_json(path):
        requested_path["value"] = path
        return payload

    monkeypatch.setattr(client._http, "get_json", fake_get_json)

    detectors = client.list_detectors()

    assert requested_path["value"] == "/v1/detectors"
    assert isinstance(detectors, list)
    assert [det.id for det in detectors] == ["det-1", "det-2"]
    assert detectors[0].status == "active"
    assert detectors[1].mode == "count"
