import json
import typer

from .client import IntelliOptics

app = typer.Typer(add_completion=False)


def _client() -> IntelliOptics:
    return IntelliOptics()


@app.command()
def status() -> None:
    client = _client()
    print(json.dumps({"ok": True, "endpoint": client.base_url}, indent=2))


@app.command()
def whoami() -> None:
    client = _client()
    print(json.dumps(client.whoami(), indent=2))
