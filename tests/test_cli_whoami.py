import json

import responses
from typer.testing import CliRunner

from intellioptics.cli import app


def test_cli_whoami_pretty_print():
    runner = CliRunner()
    endpoint = "https://api.example.test"
    token = "test-token"
    identity = {
        "id": "user-123",
        "name": "Ada Lovelace",
        "email": "ada@example.test",
        "roles": ["admin", "engineer"],
    }

    with responses.RequestsMock(assert_all_requests_are_fired=True) as rsps:
        rsps.get(
            f"{endpoint}/v1/users/me",
            json=identity,
            match=[responses.matchers.header_matcher({"Authorization": f"Bearer {token}"})],
        )

        result = runner.invoke(
            app,
            ["whoami"],
            env={
                "INTELLIOPTICS_ENDPOINT": endpoint,
                "INTELLIOOPTICS_API_TOKEN": token,
                "INTELLIOPTICS_API_TOKEN": token,
            },
        )

    assert result.exit_code == 0, result.stdout
    expected_output = json.dumps(identity, indent=2, sort_keys=True) + "\n"
    assert result.stdout == expected_output
