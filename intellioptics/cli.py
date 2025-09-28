"""Command line interface for interacting with the IntelliOptics API."""

from __future__ import annotations

import json
import os

import typer

from .client import IntelliOptics

app = typer.Typer(add_completion=False)


def _client() -> IntelliOptics:
    """Construct an :class:`IntelliOptics` client using environment variables."""

    api_token = os.getenv("INTELLIOPTICS_API_TOKEN") or os.getenv("INTELLIOOPTICS_API_TOKEN")
    if not api_token:
        typer.echo("INTELLIOPTICS_API_TOKEN environment variable is required", err=True)
        raise typer.Exit(code=1)

    endpoint = os.getenv("INTELLIOPTICS_ENDPOINT")
    disable_tls = os.getenv("DISABLE_TLS_VERIFY") == "1"

    return IntelliOptics(
        endpoint=endpoint,
        api_token=api_token,
        disable_tls_verification=disable_tls,
    )


@app.command()
def status() -> None:
    """Print basic environment information."""

    typer.echo(
        json.dumps(
            {
                "ok": True,
                "endpoint": os.getenv("INTELLIOPTICS_ENDPOINT"),
            },
            indent=2,
        )
    )


@app.command()
def whoami() -> None:
    """Return the identity associated with the configured API token."""

    identity = _client().whoami()
    serializer = getattr(identity, "model_dump", None) or getattr(identity, "dict", None)
    payload = serializer() if serializer else identity
    typer.echo(json.dumps(payload, indent=2))


if __name__ == "__main__":  # pragma: no cover
    app()
