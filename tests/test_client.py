import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError
from intellioptics.models import UserIdentity, FeedbackIn


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


def test_submit_feedback_posts_feedback_payload(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    payload_capture = {}

    def fake_post_json(path, *, json):
        payload_capture["path"] = path
        payload_capture["json"] = json
        return {"status": "ok"}

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    result = client.submit_feedback(
        image_query_id="iq-123",
        correct_label="YES",
        bboxes=[{"x": 1, "y": 2, "width": 3, "height": 4}],
    )

    assert payload_capture["path"] == "/v1/feedback"
    assert payload_capture["json"] == {
        "image_query_id": "iq-123",
        "correct_label": "YES",
        "bboxes": [{"x": 1, "y": 2, "width": 3, "height": 4}],
    }
    assert result == {"status": "ok"}


def test_submit_feedback_handles_empty_response(monkeypatch):
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")

    def fake_post_json(path, *, json):
        assert path == "/v1/feedback"
        assert json == {"image_query_id": "iq-456", "correct_label": "NO"}
        raise ValueError("No JSON object could be decoded")

    monkeypatch.setattr(client._http, "post_json", fake_post_json)

    feedback = FeedbackIn(image_query_id="iq-456", correct_label="NO")

    assert client.submit_feedback(feedback) == {}
