import json

from typer.testing import CliRunner

from intellioptics.cli import app
from intellioptics.models import UserIdentity


def test_cli_whoami_prints_json(monkeypatch):
    runner = CliRunner()

    monkeypatch.setenv("INTELLIOPTICS_ENDPOINT", "https://api.example.com")
    monkeypatch.setenv("INTELLIOPTICS_API_TOKEN", "token")

    class DummyClient:
        def whoami(self):
            return UserIdentity(
                id="user-123",
                email="user@example.com",
                name="Example User",
                tenant="tenant-456",
                roles=["admin"],
            )

    monkeypatch.setattr("intellioptics.cli.IntelliOptics", lambda **_: DummyClient())

    result = runner.invoke(app, ["whoami"])

    assert result.exit_code == 0, result.stdout
    parsed = json.loads(result.stdout)
    assert parsed["email"] == "user@example.com"
