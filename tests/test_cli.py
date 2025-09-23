from typer.testing import CliRunner

from intellioptics.cli import app


def test_whoami_requires_api_token(monkeypatch):
    runner = CliRunner()
    monkeypatch.delenv("INTELLIOPTICS_API_TOKEN", raising=False)

    result = runner.invoke(app, ["whoami"])

    assert result.exit_code == 1
    assert "INTELLIOPTICS_API_TOKEN environment variable is required" in result.output
    assert "Traceback" not in result.output
