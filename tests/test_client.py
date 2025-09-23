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


def test_create_detector_serializes_labels(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    captured = {}

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
