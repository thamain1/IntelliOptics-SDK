import os, json, typer
from .client import IntelliOptics
app = typer.Typer(add_completion=False)

def _client():
    return IntelliOptics(
        endpoint=os.getenv("INTELLIOPTICS_ENDPOINT"),
        api_token=os.getenv("INTELLIOOPTICS_API_TOKEN") or os.getenv("INTELLIOPTICS_API_TOKEN"),
    )

@app.command()
def status():
    print(json.dumps({"ok": True, "endpoint": os.getenv("INTELLIOPTICS_ENDPOINT")}, indent=2))

@app.command()
def whoami():
    identity = _client().whoami()
    serializer = getattr(identity, "model_dump", None)
    if callable(serializer):
        data = serializer()
    else:  # pragma: no cover - Pydantic v1 fallback
        data = identity.dict()
    print(json.dumps(data, indent=2))
