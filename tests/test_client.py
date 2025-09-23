import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import Detector, UserIdentity


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
