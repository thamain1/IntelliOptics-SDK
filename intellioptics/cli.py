"""Command line interface for the IntelliOptics SDK."""

import json
import os

import typer

from .client import IntelliOptics


app = typer.Typer(add_completion=False)


def _client() -> IntelliOptics:
    """Construct an :class:`IntelliOptics` client from environment variables."""

    return IntelliOptics(
        endpoint=os.getenv("INTELLIOPTICS_ENDPOINT"),
        api_token=os.getenv("INTELLIOOPTICS_API_TOKEN") or os.getenv("INTELLIOOPTICS_API_TOKEN"),
    )


@app.command()
def status() -> None:
    """Print connectivity status information."""

    print(json.dumps({"ok": True, "endpoint": os.getenv("INTELLIOOPTICS_ENDPOINT")}, indent=2))


@app.command()
def whoami() -> None:
    """Display the current identity in a human-readable format."""

    identity = _client().whoami()

    if hasattr(identity, "model_dump"):
        identity_payload = identity.model_dump(exclude_none=True)
    elif hasattr(identity, "dict"):
        identity_payload = identity.dict(exclude_none=True)
    else:
        identity_payload = identity

    print(json.dumps(identity_payload, indent=2, sort_keys=True))
