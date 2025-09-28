# IntelliOptics Python SDK

Installable client library for the IntelliOptics API.

> **Python**: 3.9+  
> **Package name**: `intellioptics`  
> **Typing**: ships with `py.typed` (PEP 561)

## Install

```bash
pip install intellioptics
```

## Auth & config

- `INTELLIOPTICS_API_TOKEN` – your API token (required)
- `INTELLIOPTICS_ENDPOINT` – API base URL (default: `http://localhost:8000`)
- Optional: `DISABLE_TLS_VERIFY=1` (dev only)

## Quickstart

```python
from intellioptics import IntelliOptics

io = IntelliOptics(api_token="YOUR_TOKEN")  # or set env vars

print("healthy?", io.health_generated())

me = io.whoami()
print("authenticated as", me.email or me.id)

det = io.create_detector(name="Widget Presence", labels=["widget", "no_widget"])
for detector in io.list_detectors():
    print(det.id, det.name)

res = io.submit_image_query(detector=det.id, image="image.jpg", wait=5.0, confidence_threshold=0.75)

iq = io.get_image_query(res["id"])
io.submit_feedback(iq_id=iq["id"], correct_label="YES", bboxes=[], notes="verified")
io.add_label(image_query_id=iq["id"], label="YES", metadata={"source": "human"})
io.close()
```

## Public API (current)

- `IntelliOptics.health()` → bool
- `IntelliOptics.health_generated()` → bool
- `IntelliOptics.create_detector(**kwargs)` → `DetectorOut`
- `IntelliOptics.list_detectors()` → `list[DetectorOut]`
- `IntelliOptics.get_detector(detector_id)` → `DetectorOut`
- `IntelliOptics.whoami()` → `UserIdentity`
- `IntelliOptics.submit_image_query(detector, image, *, wait=None, confidence_threshold=None, human_review=None, metadata=None, inspection_id=None)` → dict
- `IntelliOptics.submit_image_query_json(**kwargs)` → dict
- `IntelliOptics.get_image_query(iq_id)` → dict
- `IntelliOptics.submit_feedback(**kwargs)` → dict
- `IntelliOptics.add_label(**kwargs)` → `LabelRecord`
