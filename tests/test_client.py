import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
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

    assert requested_path["value"] == "/v1/users/me"
    assert isinstance(identity, UserIdentity)
    serializer = getattr(identity, "model_dump", identity.dict)
    assert serializer() == identity_payload


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
