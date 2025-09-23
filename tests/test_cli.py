import sys
import types

try:  # pragma: no cover - environment setup for tests
    import typer  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback used in tests
    class _StubTyperApp:
        def command(self, *args, **kwargs):
            def decorator(func):
                return func

            return decorator

    sys.modules["typer"] = types.SimpleNamespace(Typer=lambda **kwargs: _StubTyperApp())

from intellioptics import cli
from intellioptics.client import IntelliOptics


def test_cli_prefers_documented_token(monkeypatch):
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "documented-token")
    monkeypatch.setenv("INTELLIOOPTICS_API_TOKEN", "legacy-token")

    captured = {}

    class DummyClient:
        def __init__(self, endpoint=None, api_token=None, **kwargs):
            captured["endpoint"] = endpoint
            captured["api_token"] = api_token

    monkeypatch.setattr(cli, "IntelliOptics", DummyClient)

    client = cli._client()

    assert isinstance(client, DummyClient)
    assert captured["endpoint"] == "https://api.example.com"
    assert captured["api_token"] == "documented-token"


def test_cli_initializes_with_documented_token(monkeypatch):
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "documented-token")
    monkeypatch.delenv("INTELLIOOPTICS_API_TOKEN", raising=False)

    client = cli._client()

    assert isinstance(client, IntelliOptics)
