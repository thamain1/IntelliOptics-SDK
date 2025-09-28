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
    print(json.dumps(_client().whoami(), indent=2))
