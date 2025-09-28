
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
