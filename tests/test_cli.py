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
