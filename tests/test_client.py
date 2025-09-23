import json

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

    assert requested_path["value"] == "/v1/users/me"
    assert isinstance(identity, UserIdentity)
    serializer = getattr(identity, "model_dump", identity.dict)
    assert serializer() == identity_payload


def test_submit_image_query_encodes_optional_fields(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    captured = {}

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
