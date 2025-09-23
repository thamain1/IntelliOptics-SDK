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
