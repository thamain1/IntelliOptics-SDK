
import json

import pytest

try:  # pragma: no cover - optional dependency guard for test environments
    from typer.testing import CliRunner
except ModuleNotFoundError:  # pragma: no cover
    CliRunner = None  # type: ignore

try:  # pragma: no cover
    from intellioptics.cli import app
except ModuleNotFoundError as exc:  # pragma: no cover
    if exc.name == "typer":
        app = None  # type: ignore
    else:
        raise

from intellioptics.models import UserIdentity


@pytest.mark.skipif(CliRunner is None or app is None, reason="typer is not installed")
def test_whoami_command_outputs_json(monkeypatch):
    runner = CliRunner()

    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://example.com")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "secret-token")

    class FakeClient:
        def whoami(self):
            return UserIdentity(id="user-123", email="user@example.com")

    monkeypatch.setattr("intellioptics.cli._client", lambda: FakeClient())

    result = runner.invoke(app, ["whoami"])

    assert result.exit_code == 0
    parsed = json.loads(result.stdout)
    assert parsed["id"] == "user-123"
    assert parsed["email"] == "user@example.com"

import sys
import types

try:  # pragma: no cover - environment setup for tests
    import typer  # type: ignore  # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - fallback used in tests
    class _StubTyperApp:
import json
import importlib
import sys
import types

try:  # pragma: no cover - executed when Typer is installed
    import typer  # type: ignore # noqa: F401
except ModuleNotFoundError:  # pragma: no cover - executed when Typer is missing
    typer_stub = types.ModuleType("typer")

    class _DummyTyper:  # pragma: no cover - executed in tests
        def __init__(self, **kwargs):
            pass

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

    typer_stub.Typer = _DummyTyper  # type: ignore[attr-defined]
    sys.modules.setdefault("typer", typer_stub)

cli = importlib.import_module("intellioptics.cli")
whoami = cli.whoami
from intellioptics.models import UserIdentity

import sys
import types


class _TyperApp:
    def __init__(self, *args, **kwargs):
        pass

    def command(self, *args, **kwargs):
        def decorator(func):
            return func

        return decorator


typer_stub = types.ModuleType("typer")
typer_stub.Typer = _TyperApp
sys.modules.setdefault("typer", typer_stub)

from intellioptics.cli import whoami  # noqa: E402
from intellioptics.models import UserIdentity  # noqa: E402


def test_whoami_outputs_json(monkeypatch, capsys):
    identity = UserIdentity(
        id="user-123",
        email="user@example.com",
        name="Example User",
        tenant="tenant-789",
        roles=["admin", "user"],
    )


    class DummyClient:
        def whoami(self):
            return identity

    monkeypatch.setattr("intellioptics.cli._client", lambda: DummyClient())

    class FakeClient:
        def whoami(self):
            return identity

    monkeypatch.setattr("intellioptics.cli._client", lambda: FakeClient())

    whoami()

    captured = capsys.readouterr()

    data = json.loads(captured.out)
    serializer = getattr(identity, "model_dump", identity.dict)
    assert data == serializer()

    output = json.loads(captured.out)
    assert output["id"] == identity.id
    assert output["email"] == identity.email
    assert output["roles"] == identity.roles

import pytest

pytest.importorskip("typer")
from typer.testing import CliRunner

from intellioptics import cli
from intellioptics.errors import ApiTokenError


def test_cli_whoami_requires_api_token(monkeypatch):
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)
    runner = CliRunner()

    result = runner.invoke(
        cli.app,
        ["whoami"],
        env={"INTELLIOPTICS_ENDPOINT": "https://api.example.com"},
    )

    assert result.exit_code != 0
    assert isinstance(result.exception, ApiTokenError)
    assert "INTELLIOPTICS_API_TOKEN" in str(result.exception)
from typer.testing import CliRunner

from intellioptics.cli import app


def test_whoami_requires_api_token(monkeypatch):
    runner = CliRunner()
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)

    result = runner.invoke(app, ["whoami"])

    assert result.exit_code == 1
    assert "INTELLIOPTICS_API_TOKEN environment variable is required" in result.output
    assert "Traceback" not in result.output
