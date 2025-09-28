
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
