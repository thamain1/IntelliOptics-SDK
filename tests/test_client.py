import pytest

from intellioptics.client import IntelliOptics
from intellioptics.models import Detector


class StubHttpClient:
    def __init__(self, response):
        self._response = response
        self.last_request = None

    def post_json(self, path, json=None, **kwargs):
        self.last_request = {"path": path, "json": json, "kwargs": kwargs}
        return self._response


@pytest.fixture
def client():
    def _make(response):
        sdk = IntelliOptics(endpoint="https://example.com", api_token="token")
        sdk._http = StubHttpClient(response)
        return sdk

    return _make


def test_create_detector_builds_payload_and_hydrates_response(client):
    response = {
        "id": "det-123",
        "name": "An inspector",
        "mode": "binary",
        "query_text": "Is this defective?",
        "threshold": 0.9,
        "status": "active",
    }
    sdk = client(response)

    detector = sdk.create_detector(
        name="An inspector",
        mode="binary",
        query_text="Is this defective?",
        threshold=0.9,
    )

    assert sdk._http.last_request == {
        "path": "/v1/detectors",
        "json": {
            "name": "An inspector",
            "mode": "binary",
            "query_text": "Is this defective?",
            "threshold": 0.9,
        },
        "kwargs": {},
    }
    assert detector == Detector(**response)


def test_create_detector_omits_threshold_when_not_provided(client):
    response = {
        "id": "det-456",
        "name": "Counting bot",
        "mode": "count",
        "query_text": "How many widgets?",
        "threshold": 0.75,
        "status": "active",
    }
    sdk = client(response)

    detector = sdk.create_detector(
        name="Counting bot",
        mode="count",
        query_text="How many widgets?",
    )

    assert sdk._http.last_request == {
        "path": "/v1/detectors",
        "json": {
            "name": "Counting bot",
            "mode": "count",
            "query_text": "How many widgets?",
        },
        "kwargs": {},
    }
    assert detector == Detector(**response)
