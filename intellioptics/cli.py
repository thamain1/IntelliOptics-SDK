import os, json, typer
from .client import IntelliOptics
app = typer.Typer(add_completion=False)

def _client():
    return IntelliOptics(
        endpoint=os.getenv("INTELLIOPTICS_ENDPOINT"),
        api_token=os.getenv("INTELLIOPTICS_API_TOKEN"),
    )

@app.command()
def status():
    print(json.dumps({"ok": True, "endpoint": os.getenv("INTELLIOPTICS_ENDPOINT")}, indent=2))

@app.command()
def whoami():
    identity = _client().whoami()
    serializer = getattr(identity, "model_dump", None) or getattr(identity, "dict", None)
    payload = serializer() if serializer else identity
    print(json.dumps(payload, indent=2))
