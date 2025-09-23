import os, json, typer
from .client import IntelliOptics
app = typer.Typer(add_completion=False)

def _client():
    """Construct an :class:`IntelliOptics` client using environment variables."""

    api_token = os.getenv("INTELLIOPTICS_API_TOKEN")
    if api_token is None:
        # Backwards compatibility with the historical misspelled variable name.
        api_token = os.getenv("INTELLIOOPTICS_API_TOKEN")

    return IntelliOptics(
        endpoint=os.getenv("INTELLIOPTICS_ENDPOINT"),
        api_token=api_token,
    )

@app.command()
def status():
    print(json.dumps({"ok": True, "endpoint": os.getenv("INTELLIOPTICS_ENDPOINT")}, indent=2))

@app.command()
def whoami():
    print(json.dumps(_client().whoami(), indent=2))
