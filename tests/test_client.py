import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import UserIdentity


def _make_client():
    return IntelliOptics(endpoint="https://api.example.com", api_token="token")


def test_init_requires_api_token():
    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://api.example.com")


def test_whoami_returns_user_identity(monkeypatch):
    client = _make_client()

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


def test_submit_image_query_serializes_optional_fields(monkeypatch):
    client = _make_client()

    captured = {}

    def fake_post_json(path, **kwargs):
        captured["path"] = path
        captured["kwargs"] = kwargs
        return {
            "id": "iq-123",
            "detector_id": "det-1",
            "status": "PENDING",
        }

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    iq = client.submit_image_query(
        detector="det-1",
        image=None,
        prompt="Inspect welds",
        wait=2.5,
        confidence_threshold=0.85,
        metadata={"source": "field"},
        inspection_id="insp-77",
    )

    assert captured["path"] == "/v1/image-queries"
    data = captured["kwargs"]["data"]
    assert data["prompt"] == "Inspect welds"
    assert data["wait"] == 2.5
    assert data["confidence_threshold"] == 0.85
    assert data["inspection_id"] == "insp-77"
    assert data["metadata"] == "{\"source\": \"field\"}"
    assert "files" not in captured["kwargs"] or captured["kwargs"]["files"] is None
    assert iq.id == "iq-123"
