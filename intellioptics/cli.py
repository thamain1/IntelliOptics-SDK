import os, json, typer
from .client import IntelliOptics
app = typer.Typer(add_completion=False)

def _client():
    api_token = os.getenv("INTELLIOPTICS_API_TOKEN")
    if not api_token:
        typer.echo("INTELLIOPTICS_API_TOKEN environment variable is required")
        raise typer.Exit(code=1)
    return IntelliOptics(
        endpoint=os.getenv("INTELLIOPTICS_ENDPOINT"),
        api_token=os.getenv("INTELLIOPTICS_API_TOKEN"),
        api_token=api_token,
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

    if serializer is None:
        serializer = identity.dict
    data = serializer()

    print(json.dumps(data, indent=2))
