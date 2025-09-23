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


def test_submit_image_query_forwards_metadata(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    captured = {}

    def fake_post_json(path, *, files=None, data=None, **kwargs):
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
