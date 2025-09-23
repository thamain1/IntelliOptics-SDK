import os, json, typer
from .client import IntelliOptics
app = typer.Typer(add_completion=False)

def _client():
    return IntelliOptics(
        endpoint=os.getenv("INTELLIOPTICS_ENDPOINT"),
    )

@app.command()
def status():
    print(json.dumps({"ok": True, "endpoint": os.getenv("INTELLIOPTICS_ENDPOINT")}, indent=2))

@app.command()
def whoami():
    print(json.dumps(_client().whoami(), indent=2))
