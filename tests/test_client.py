import pytest

from intellioptics.client import IntelliOptics
from intellioptics.errors import ApiTokenError


def test_init_requires_api_token(monkeypatch):
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)

    with pytest.raises(ApiTokenError):
        IntelliOptics(endpoint="https://example.com")


def test_init_uses_environment(monkeypatch):
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "env-token")
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://example.com")

    client = IntelliOptics()

    assert client._http.headers["Authorization"] == "Bearer env-token"
