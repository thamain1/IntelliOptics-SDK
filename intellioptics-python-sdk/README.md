# IntelliOptics Python SDK

```python
from intellioptics import IntelliOptics

io = IntelliOptics(endpoint="https://YOUR-ENDPOINT", api_token="YOUR_TOKEN")
iq_id = io.ask_async(detector="det-123", image_url="https://example.com/image.jpg")
iq = io.wait_for_confident_result(iq_id, threshold=0.9, timeout_sec=30)
print(iq.status, iq.result)
```

## Build
```
python -m pip install -U pip build
python -m build
```