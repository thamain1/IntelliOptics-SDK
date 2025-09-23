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

    typer_stub.Typer = _DummyTyper  # type: ignore[attr-defined]
    sys.modules.setdefault("typer", typer_stub)

cli = importlib.import_module("intellioptics.cli")
whoami = cli.whoami
from intellioptics.models import UserIdentity


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

    whoami()

    captured = capsys.readouterr()
    data = json.loads(captured.out)
    serializer = getattr(identity, "model_dump", identity.dict)
    assert data == serializer()
