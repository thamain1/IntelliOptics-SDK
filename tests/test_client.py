import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import UserIdentity, Detector, ImageQuery


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
