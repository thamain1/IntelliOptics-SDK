# IntelliOptics SDK & CLI

The IntelliOptics SDK is a lightweight Python client for interacting with the IntelliOptics
computer-vision platform. It provides both a programmatic API for building rich integrations and
an ergonomic command line interface (CLI) for quick diagnostics.

## Key features

- **Pythonic client** for creating detectors, submitting image queries, polling for results, and
  managing human labels.
- **Environment-aware configuration** that respects standard `INTELLIOPTICS_*` environment
  variables for endpoints, tokens, and TLS behaviour.
- **Typer-powered CLI** with built-in commands for checking connectivity and verifying your API
  identity.
- **Automatic image handling** that converts many in-memory and on-disk image formats into JPEG
  payloads that are ready for upload.

## Installation

The SDK targets Python 3.9 and later. Install it directly from the repository root using `pip`:

```bash
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

Alternatively, package consumers can install the distributed wheel:

```bash
pip install intellioptics
```

> **Note:** The project declares the following runtime dependencies: `requests`, `pydantic (<3)`,
> `Pillow`, and `typer`.

### Installing from Git (including Docker builds)

When installing directly from the repository—whether on a workstation or in a Dockerfile—point
`pip` at the repository root. Earlier iterations of the project kept a `python-sdk/` subdirectory,
but that folder has been removed; attempting to install via
`#subdirectory=python-sdk` now fails with `neither 'setup.py' nor 'pyproject.toml' found`.

To install the current SDK straight from GitHub:

```bash
pip install "intellioptics @ git+https://github.com/thamain1/IntelliOptics.git@main"
```

Pin to a specific tag or commit when you need a reproducible build:

```bash
pip install "intellioptics @ git+https://github.com/thamain1/IntelliOptics.git@38533a4c1807583422bdb402599eff5fb81d311d"
```

In Dockerfiles, a typical snippet looks like:

```dockerfile
RUN python -m pip install --upgrade pip \
    && pip install "intellioptics @ git+https://github.com/thamain1/IntelliOptics.git@main"
```

This ensures `pip` discovers the `pyproject.toml` in the repository root and installs the modern
package layout.

## Repository layout

Only the modern SDK that powers the published `intellioptics` package is kept in this repository.
Legacy scaffolds (`sdk/`, `intellioptics-python-sdk/`, and `python-sdk/`) have been removed so the
active codebase lives under `intellioptics/` alongside its tests and packaging metadata. See
[`docs/CLIENT_OVERVIEW.md`](docs/CLIENT_OVERVIEW.md) for a snapshot of the retained client module.
The streamlined tree now looks like this:

```text
intellioptics/          # Runtime package (client, HTTP helpers, models, CLI)
tests/                  # Test suite exercising the public surface area
pyproject.toml          # Packaging definition for the published SDK
```

If you need to reference the old iterations, retrieve them from git history prior to this
consolidation.

## Configuration

The SDK and CLI are configured through environment variables:

| Variable | Description |
| --- | --- |
| `INTELLIOPTICS_ENDPOINT` | Base URL of the IntelliOptics API (for example `https://intellioptics-api-37558.azurewebsites.net`). |
| `INTELLIOPTICS_API_TOKEN` | Personal access token used for authenticating requests. This is the same variable consumed by the CLI when instantiating its client. |
| `DISABLE_TLS_VERIFY` | Optional. Set to `1` to skip TLS certificate verification (useful for local testing). |


## Command line interface

Once installed, the CLI entrypoint is available as `intellioptics`. It reads the same
environment variables as the Python client (`INTELLIOPTICS_ENDPOINT`,
`INTELLIOPTICS_API_TOKEN`, and optional `DISABLE_TLS_VERIFY`):

```bash
# Verify that your environment variables are wired up
$ export INTELLIOPTICS_ENDPOINT="https://intellioptics-api-37558.azurewebsites.net"
$ export INTELLIOPTICS_API_TOKEN="your-token"
$ intellioptics status
{
  "ok": true,
  "endpoint": "https://intellioptics-api-37558.azurewebsites.net"
}

# Check the identity associated with the current API token
$ intellioptics whoami
{
  "id": "user-123",
  "email": "user@example.com",
  "roles": ["admin", "user"],
  "tenant": "tenant-789"
}
```

Additional commands can be added over time; run `intellioptics --help` to discover what is
available in your version of the tool.

## Using the Python SDK

Instantiate the `IntelliOptics` client either by providing explicit parameters or by relying on the
configured environment variables:

```python
from intellioptics import IntelliOptics

client = IntelliOptics(
    endpoint="https://intellioptics-api-37558.azurewebsites.net",
    api_token="your-token",
)

# List existing detectors
for detector in client.list_detectors():
    print(detector.id, detector.name)

# Create a new multiclass detector with label hints
my_detector = client.create_multiclass_detector(
    "safety-inspections",
    "Identify required safety gear",
    class_names=["ppe", "no_ppe"],
)

# Submit an image for automated analysis
with open("inspection.jpg", "rb") as image_file:
    query = client.submit_image_query(
        detector=my_detector.id,
        image=image_file,
        prompt="Identify required safety gear",
        wait=1.0,
        metadata={"site": "plant-a", "shift": 2},
    )

# Poll until the model is confident enough (defaults to 90%)
confident = client.wait_for_confident_result(query, confidence_threshold=0.95)
print(confident.status, confident.label, confident.confidence)

# Responses now expose the canonical ImageQuery payload used throughout the SDK.
print(confident.model_dump())
# {'id': 'iq-123', 'detector_id': 'det-456', 'status': 'DONE', 'label': 'ppe', 'confidence': 0.98}
```

Successful calls to the image query endpoints now emit payloads that mirror the SDK models. A
typical response looks like:

```json
{
  "id": "iq-123",
  "detector_id": "det-456",
  "status": "DONE",
  "result_type": "binary",
  "label": "YES",
  "confidence": 0.97,
  "extra": {
    "latency_ms": 420,
    "model_version": "demo-v0"
  }
}
```

### Image query payloads

The API provides two entry-points for submitting imagery:

- `POST /v1/image-queries` expects `multipart/form-data`. Non-binary fields are simple form fields,
  so numeric inputs such as `wait` (seconds to hold the HTTP connection) and `confidence_threshold`
  should be provided as plain values that can be parsed as floats. If you need to attach structured
  `metadata`, JSON-encode it yourself (for example `{"metadata": json.dumps({...})}`) before adding
  it to the form body. String fields such as `prompt` or `inspection_id` can be included directly.
- `POST /v1/image-queries-json` accepts an `application/json` payload. In this mode the same fields
  are provided with their natural JSON types (e.g. `wait`/`confidence_threshold` as numbers and
  `metadata` as a nested JSON object). This endpoint is convenient when the image is already hosted
  elsewhere and you only need to pass references plus metadata.

The helper functions `ask_ml` and `ask_confident` wrap common flows for asynchronous and
confidence-thresholded queries. When you need ground-truth data, call `add_label` to attach human
labels (optionally with metadata) to a given image query.

#### Multipart field reference

`POST /v1/image-queries` accepts `multipart/form-data` payloads. The SDK automatically builds the
multipart body, but when constructing the request manually submit fields using the following
conventions:

- `detector_id` (**required**) – string identifier of the detector to run.
- `prompt` (optional) – free-form text prompt that can guide analysis.
- `wait` (optional, default `0`) – number of seconds to wait for a synchronous response before
  returning immediately.
- `confidence_threshold` (optional) – float representing the minimum confidence required before the
  backend marks a result as complete.
- `metadata` (optional) – JSON-encoded string. When submitting multipart bodies, serialize your
  structured metadata with `json.dumps` and send the resulting text value.
- `inspection_id` (optional) – string correlation identifier for downstream systems.
- `image` (optional) – binary file part containing the image payload.

For `POST /v1/image-queries-json`, send the same fields inside an `application/json` body. In that
variant `metadata` is an object rather than a JSON string, so include it directly as nested JSON
data.

### Working with images

The SDK transparently converts a variety of image inputs (file paths, bytes, file-like objects,
Pillow `Image` instances, or NumPy arrays) into uploadable JPEG blobs via
`intellioptics._img.to_jpeg_bytes`. This means you can pass the most convenient form for your
workflow without writing conversion code yourself.

### Error handling

- `ApiTokenError` is raised when the client cannot locate an API token during initialization.
- `IntelliOpticsClientError` wraps HTTP errors returned by the remote API and includes status codes
  and response text to aid debugging.

### Async usage

An asynchronous variant of the client is also available:

```python
from intellioptics import AsyncIntelliOptics

async def run_check() -> None:
    async with AsyncIntelliOptics(api_token="your-token") as client:
        status = await client.whoami()
        print(status.email)

# asyncio.run(run_check())
```

## Testing

Run the test suite with `pytest` to validate the SDK behaviour before publishing:

```bash
pytest
```

## Support

For issues, feedback, or feature requests, please contact jmorgan@4wardmotions.con.
