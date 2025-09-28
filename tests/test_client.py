import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
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
from intellioptics.models import UserIdentity


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
