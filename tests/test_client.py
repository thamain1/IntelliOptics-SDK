from pathlib import Path
from unittest.mock import Mock

import pytest

import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from intellioptics.client import IntelliOptics
from intellioptics.models import FeedbackIn


@pytest.fixture
def client():
    client = IntelliOptics(endpoint="https://api.example.com", api_token="token")
    client._http = Mock()
    return client


def test_submit_feedback_posts_payload(client):
    feedback = FeedbackIn(
        image_query_id="iq-123",
        correct_label="YES",
        bboxes=[{"x": 1, "y": 2, "w": 3, "h": 4}],
    )
    client._http.post_json.return_value = {"status": "ok"}

    response = client.submit_feedback(feedback)

    client._http.post_json.assert_called_once_with(
        "/v1/feedback",
        json={
            "image_query_id": "iq-123",
            "correct_label": "YES",
            "bboxes": [{"x": 1, "y": 2, "w": 3, "h": 4}],
        },
    )
    assert response == {"status": "ok"}


def test_submit_feedback_with_kwargs_and_empty_response(client):
    client._http.post_json.return_value = {}

    response = client.submit_feedback(image_query_id="iq-456", correct_label="NO")

    client._http.post_json.assert_called_once_with(
        "/v1/feedback",
        json={"image_query_id": "iq-456", "correct_label": "NO"},
    )
    assert response == {}
