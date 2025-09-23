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


def test_submit_image_query_normalizes_answer_out(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    answer_payload = {
        "image_query_id": "iq-123",
        "answer": "YES",
        "confidence": 0.91,
        "latency_ms": 420,
        "model_version": "demo-v0",
    }

    def fake_post_json(path, **_):
        assert path == "/v1/image-queries"
        return answer_payload

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    query = client.submit_image_query(detector="det-456")

    assert query.id == "iq-123"
    assert query.status == "DONE"
    assert query.label == "YES"
    assert query.confidence == answer_payload["confidence"]
    assert query.extra == {"latency_ms": 420, "model_version": "demo-v0"}


def test_get_result_normalizes_structured_payload(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    api_payload = {
        "id": "iq-789",
        "status": "PROCESSING",
        "detector_id": "det-1",
        "result_type": "binary",
        "result": {"label": "NO", "confidence": 0.55, "count": 2},
    }

    def fake_get_json(path):
        assert path == "/v1/image-queries/iq-789"
        return api_payload

    monkeypatch.setattr(client._http, "get_json", fake_get_json)

    result = client.get_result("iq-789")

    assert result.id == "iq-789"
    assert result.status == "PROCESSING"
    assert result.label == "NO"
    assert result.confidence == 0.55
    assert result.extra == {"count": 2}
