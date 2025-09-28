import json
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

    class FakeClient:
        def whoami(self):
            return identity

    monkeypatch.setattr("intellioptics.cli._client", lambda: FakeClient())

    whoami()

    captured = capsys.readouterr()
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
