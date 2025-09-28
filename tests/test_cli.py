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
