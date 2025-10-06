# IntelliOptics client module overview

Following the repository cleanup, the project now ships a single supported client implementation:
`intellioptics/client.py`. This module backs both the synchronous and asynchronous SDK surfaces
and is the code that is published to PyPI as part of the `intellioptics` package.

## What is retained

The module exposes two entry points that users import from `intellioptics`:

- `IntelliOptics` – a synchronous convenience wrapper around the HTTP transport.
- `AsyncIntelliOptics` – the asynchronous variant built on `httpx.AsyncClient`.

Both classes share helpers for detector lifecycle management, image-query submission and polling,
alert orchestration, payload templates, human-review toggles, and user identity lookups. Supporting
utilities such as `_detector_identifier`, `_build_image_query_request`, and
`wait_for_confident_result` are part of the same file so downstream code only needs to depend on a
single module.

```text
intellioptics/
└── client.py
    ├── IntelliOptics          # sync high-level client
    ├── AsyncIntelliOptics     # async high-level client
    ├── wait_for_confident_result()
    ├── submit_image_query()
    ├── list_detectors()
    ├── create_binary_detector()
    ├── create_multiclass_detector()
    ├── configure_alert()
    └── ...                    # additional workflow helpers
```

All other legacy client variants that used to live under `sdk/`, `intellioptics-python-sdk/`, and
`python-sdk/` have been removed. Their features are either superseded by or directly implemented in
`client.py`.

## Interface snapshot

Below is a condensed excerpt of the public surface so you can confirm what ships after the
consolidation:

```python
from intellioptics.client import IntelliOptics, AsyncIntelliOptics, ExperimentalApi

__all__ = ["IntelliOptics", "AsyncIntelliOptics", "ExperimentalApi"]
```

Within the file you will find:

- strong typing via Pydantic models (`Detector`, `ImageQuery`, `Action`, `Rule`, etc.),
- request builders that convert images and metadata into multipart payloads,
- synchronous and asynchronous HTTP client composition,
- polling helpers (`wait_for_confident_result`, `wait_for_result`) that originated from the older
  scaffolds and were merged here,
- Azure-friendly defaults (`https://intellioptics-api-37558.azurewebsites.net`) and environment-based
  token discovery.

This is the canonical client that downstream services, Helm deployments, and the CLI should import.
