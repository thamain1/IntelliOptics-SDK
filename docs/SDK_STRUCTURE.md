# IntelliOptics SDK structure

This repository now focuses exclusively on the packaged `intellioptics` SDK. The code layout is
intended to be easy to navigate when extending the client or troubleshooting deployments. If you
need a quick refresher on the supported client implementation, review
[`CLIENT_OVERVIEW.md`](CLIENT_OVERVIEW.md).

## Package modules

- `intellioptics/_http.py` – shared HTTP client wrappers that handle authentication, retries, and
  TLS configuration.
- `intellioptics/_img.py` – helpers for normalising common image inputs (paths, bytes, Pillow
  instances, and NumPy arrays) into upload-ready JPEG payloads.
- `intellioptics/client.py` – the high-level synchronous and asynchronous client surfaces, including
  detector management, image query submission, alert configuration, and experimental APIs.
- `intellioptics/models.py` – Pydantic models that mirror the wire format returned by the hosted
  IntelliOptics service.
- `intellioptics/cli.py` – Typer-based command-line entry point used by `intellioptics` on the
  command line.

## Tests

`tests/` contains focused unit tests that exercise the public client surface area and the supporting
image helpers. Run `pytest` before publishing changes to ensure compatibility across environments.

## Packaging helper

The only maintained script for producing a distributable zip of the SDK is
[`make_io_sdk_zip.ps1`](../make_io_sdk_zip.ps1). Older throwaway bootstrap scripts (such as the
duplicate that lived under `intellioptics_sdk/`) have been deleted so that contributors have a single
trusted entry point when preparing ad-hoc builds.

## Legacy scaffolds

Older experimental SDK scaffolds have been removed from the repository to reduce confusion. If you
need to reference them, check out a commit prior to this cleanup (for example `git show
<old-sha>:sdk/intellioptics/client.py`).

This consolidation keeps the main branch aligned with the published package and makes it easier to
ship updates to Azure, Kubernetes, and Helm based deployments.
