import base64
import sys
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from intellioptics.client import IntelliOptics
from intellioptics.models import ImageQuery


@pytest.fixture()
def client():
    return IntelliOptics(endpoint="https://api.example.com", api_token="token")


def test_submit_image_query_form_fields(client):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "id": "iq_123",
        "detector_id": "det-1",
        "status": "PENDING",
    }

    image_bytes = b"fake-jpeg"

    with patch("intellioptics._http.requests.post", return_value=mock_response) as mock_post:
        result = client.submit_image_query(detector="det-1", image=image_bytes, wait=False)

    assert isinstance(result, ImageQuery)
    assert result.id == "iq_123"

    assert mock_post.call_args.kwargs["data"] == {"detector_id": "det-1", "wait": "false"}

    files = mock_post.call_args.kwargs["files"]
    assert "image" in files
    filename, payload, content_type = files["image"]
    assert filename == "image.jpg"
    assert payload == image_bytes
    assert content_type == "image/jpeg"


def test_submit_image_query_json_payload(client):
    mock_response = Mock()
    mock_response.ok = True
    mock_response.json.return_value = {
        "id": "iq_456",
        "detector_id": "det-2",
        "status": "PENDING",
    }

    image_payload = base64.b64encode(b"jpeg").decode()

    with patch("intellioptics._http.requests.post", return_value=mock_response) as mock_post:
        result = client.submit_image_query_json(detector="det-2", image=image_payload, wait=True)

    assert isinstance(result, ImageQuery)
    assert result.id == "iq_456"

    assert mock_post.call_args.kwargs["json"] == {
        "detector_id": "det-2",
        "image": image_payload,
        "wait": True,
    }
    assert "files" not in mock_post.call_args.kwargs
