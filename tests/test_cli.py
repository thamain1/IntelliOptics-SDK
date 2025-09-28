from __future__ import annotations

import json
from typing import Any

import pytest
import typer
from typer.testing import CliRunner

from intellioptics import cli
from intellioptics.models import UserIdentity


@pytest.fixture()
def runner() -> CliRunner:
    return CliRunner()


def test_client_prefers_documented_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "documented-token")
    monkeypatch.setenv("INTELLIOOPTICS_API_TOKEN", "legacy-token")

    captured: dict[str, Any] = {}

    class DummyClient:
        def __init__(self, endpoint: str | None = None, api_token: str | None = None, **_: Any) -> None:
            captured["endpoint"] = endpoint
            captured["api_token"] = api_token

    monkeypatch.setattr(cli, "IntelliOptics", DummyClient)

    client = cli._client()

    assert isinstance(client, DummyClient)
    assert captured["endpoint"] == "https://api.example.com"
    assert captured["api_token"] == "documented-token"


def test_client_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)
    monkeypatch.delenv("INTELLIOOPTICS_API_TOKEN", raising=False)

    with pytest.raises(typer.Exit) as exc:
        cli._client()

    assert exc.value.exit_code == 1


@pytest.mark.usefixtures("runner")
def test_whoami_command_outputs_json(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "token")

    identity = UserIdentity(id="user-123", email="user@example.com", roles=["admin"])

    class DummyClient:
        def whoami(self) -> UserIdentity:
            return identity

    monkeypatch.setattr(cli, "_client", lambda: DummyClient())

    result = runner.invoke(cli.app, ["whoami"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    serializer = getattr(identity, "model_dump", identity.dict)
    assert payload == serializer()


@pytest.mark.usefixtures("runner")
def test_status_command_reports_endpoint(monkeypatch: pytest.MonkeyPatch, runner: CliRunner) -> None:
    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://api.example.com")

    result = runner.invoke(cli.app, ["status"])

    assert result.exit_code == 0
    payload = json.loads(result.stdout)
    assert payload == {"ok": True, "endpoint": "https://api.example.com"}
