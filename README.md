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

## Configuration

The SDK and CLI are configured through environment variables:

| Variable | Description |
| --- | --- |
| `INTELLIOPTICS_ENDPOINT` | Base URL of the IntelliOptics API (for example `https://intellioptics-api-37558.azurewebsites.net`). |
| `INTELLIOPTICS_API_TOKEN` | Personal access token used for authenticating requests. |
| `DISABLE_TLS_VERIFY` | Optional. Set to `1` to skip TLS certificate verification (useful for local testing). |


## Command line interface

Once installed, the CLI entrypoint is available as `intellioptics`:

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
    endpoint="https:intellioptics-api-37558.azurewebsites.net",
    api_token="your-token",
)

# List existing detectors
for detector in client.list_detectors():
    print(detector.id, detector.name)

# Create a new detector with optional label hints
my_detector = client.create_detector("safety-inspections", labels=["ppe", "no_ppe"])

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
```

The helper functions `ask_ml` and `ask_confident` wrap common flows for asynchronous and
confidence-thresholded queries. When you need ground-truth data, call `add_label` to attach human
labels (optionally with metadata) to a given image query.

### Image query payloads

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

## Testing

Run the test suite with `pytest` to validate the SDK behaviour before publishing:

```bash
pytest
```

## Support

For issues, feedback, or feature requests, please contact the IntelliOptics team through your
customer support channel or reach out to your IntelliOptics solutions engineer.
