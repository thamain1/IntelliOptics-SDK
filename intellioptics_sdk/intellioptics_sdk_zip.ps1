# Where to drop the zip
$DestRoot = "C:\Users\ThaMain1\IntelliOptics"
$ProjectName = "intellioptics-python-sdk"
$TempRoot = Join-Path $env:TEMP "$ProjectName-build"
$ZipPath = Join-Path $DestRoot "$ProjectName.zip"

# Clean temp
if (Test-Path $TempRoot) { Remove-Item -Recurse -Force $TempRoot }
New-Item -ItemType Directory -Force $TempRoot | Out-Null
New-Item -ItemType Directory -Force (Join-Path $TempRoot "src\intellioptics") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $TempRoot "tests") | Out-Null
New-Item -ItemType Directory -Force (Join-Path $TempRoot ".github\workflows") | Out-Null

# ---------- Files ----------
@'
[build-system]
requires = ["hatchling>=1.25"]
build-backend = "hatchling.build"

[project]
name = "intellioptics"
version = "0.1.0"
description = "Official Python SDK for the IntelliOptics API"
readme = "README.md"
requires-python = ">=3.10"
authors = [{ name = "4wardmotions", email = "dev@4wardmotions.com" }]
license = { text = "Proprietary" }
dependencies = [
  "httpx>=0.28.0",
  "pydantic>=2.7.0",
  "typing-extensions>=4.8.0"
]

[project.optional-dependencies]
test = ["pytest>=7.4", "respx>=0.21.1", "pytest-asyncio>=0.23"]

[project.urls]
Homepage = "https://4wardmotions.com"
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot "pyproject.toml")

@'
# IntelliOptics Python SDK

```python
from intellioptics import IntelliOptics

io = IntelliOptics(endpoint="https://YOUR-ENDPOINT", api_token="YOUR_TOKEN")

# submit by URL
iq_id = io.ask_async(detector="det-123", image_url="https://example.com/image.jpg")

# wait for result
iq = io.wait_for_confident_result(iq_id, threshold=0.9, timeout_sec=30)
print(iq.status, iq.result)
Build locally
nginx
Copy
Edit
python -m pip install -U pip build
python -m build
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot "README.md")

@'
from .client import IntelliOptics, AsyncIntelliOptics, ExperimentalApi
from .models import ImageQuery, ImageQueryResult
from .exceptions import IntelliOpticsError, ApiError, AuthError, NotFound

all = [
"IntelliOptics", "AsyncIntelliOptics", "ExperimentalApi",
"ImageQuery", "ImageQueryResult",
"IntelliOpticsError", "ApiError", "AuthError", "NotFound",
]

version = "0.1.0"
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot "src\intellioptics_init_.py")

@'
class IntelliOpticsError(Exception):
pass

class AuthError(IntelliOpticsError):
pass

class NotFound(IntelliOpticsError):
pass

class ApiError(IntelliOpticsError):
def init(self, status: int, message: str, payload=None):
super().init(f"{status}: {message}")
self.status = status
self.payload = payload
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot "src\intellioptics\exceptions.py")

@'
from typing import Any, Optional
from pydantic import BaseModel, Field

class ImageQueryResult(BaseModel):
label: Optional[str] = None
confidence: Optional[float] = None
count: Optional[int] = None
extra: Optional[dict[str, Any]] = None

class ImageQuery(BaseModel):
id: str
status: str = Field(default="PROCESSING") # PROCESSING | DONE | FAILED
result_type: Optional[str] = None
done_processing: bool = False
result: Optional[ImageQueryResult] = None
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot "src\intellioptics\models.py")

@'
from future import annotations
import os, time, asyncio
from typing import Any, Optional
import httpx
from .exceptions import ApiError, AuthError, NotFound
from .models import ImageQuery, ImageQueryResult

_DEFAULT_TIMEOUT = float(os.getenv("INTELLIOPTICS_TIMEOUT", "30"))
_UA = "intellioptics-sdk/0.1.0 (+https://4wardmotions.com)"

def _headers(token: str | None) -> dict[str,str]:
h = {"Accept": "application/json", "User-Agent": _UA}
if token: h["Authorization"] = f"Bearer {token}"
return h

def _handle(resp: httpx.Response) -> dict:
if resp.status_code == 401: raise AuthError("Unauthorized")
if resp.status_code == 404: raise NotFound("Resource not found")
if resp.status_code >= 400:
try: msg = resp.json()
except Exception: msg = resp.text
raise ApiError(resp.status_code, str(msg), msg)
return resp.json()

class IntelliOptics:
"""Synchronous client for IntelliOptics HTTP API."""
def init(self, endpoint: str, api_token: Optional[str]=None, timeout: float=_DEFAULT_TIMEOUT):
self.base = endpoint.rstrip("/")
self.token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
self._c = httpx.Client(timeout=timeout, headers=_headers(self.token))

python
Copy
Edit
def close(self): self._c.close()

def ask_async(self, detector: str, image_url: Optional[str]=None,
              image_path: Optional[str]=None, image_bytes: Optional[bytes]=None,
              metadata: Optional[dict[str,Any]]=None) -> str:
    url = f"{self.base}/v1/image-queries"
    if image_url:
        payload = {"detector_id": detector, "image_url": image_url}
        if metadata: payload["metadata"] = metadata
        data = _handle(self._c.post(url, json=payload))
    else:
        if image_path and not image_bytes:
            with open(image_path, "rb") as f: image_bytes = f.read()
        files = {"image": ("image.jpg", image_bytes or b"", "application/octet-stream")}
        form = {"detector_id": detector}
        if metadata: form["metadata"] = httpx.JSONEncoder().encode(metadata)
        data = _handle(self._c.post(url, data=form, files=files))
    return data.get("id") or data.get("image_query_id")

def get_image_query(self, iq_id: str) -> ImageQuery:
    data = _handle(self._c.get(f"{self.base}/v1/image-queries/{iq_id}"))
    r = data.get("result") or {}
    return ImageQuery(
        id=data.get("id", iq_id),
        status=("DONE" if data.get("done_processing") else data.get("status", "PROCESSING")),
        result_type=data.get("result_type"),
        done_processing=bool(data.get("done_processing")),
        result=ImageQueryResult(
            label=r.get("label"),
            confidence=r.get("confidence"),
            count=r.get("count") or r.get("value"),
            extra={k:v for k,v in r.items() if k not in {"label","confidence","count","value"}} or None,
        ) if r else None,
    )

def wait_for_confident_result(self, iq_id: str, threshold: float=0.9, timeout_sec: float=30, poll_interval: float=1.0) -> ImageQuery:
    deadline = time.time() + timeout_sec
    last = None
    while time.time() < deadline:
        last = self.get_image_query(iq_id)
        r = last.result
        if r and r.label and (r.confidence or 0) >= threshold: return last
        if last.done_processing: return last
        time.sleep(poll_interval)
    return last or self.get_image_query(iq_id)
class AsyncIntelliOptics:
"""Async client for IntelliOptics HTTP API."""
def init(self, endpoint: str, api_token: Optional[str]=None, timeout: float=_DEFAULT_TIMEOUT):
self.base = endpoint.rstrip("/")
self.token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
self._c = httpx.AsyncClient(timeout=timeout, headers=_headers(self.token))

python
Copy
Edit
async def aclose(self): await self._c.aclose()

async def ask_async(self, detector: str, image_url: Optional[str]=None,
                    image_bytes: Optional[bytes]=None, metadata: Optional[dict[str,Any]]=None) -> str:
    url = f"{self.base}/v1/image-queries"
    if image_url:
        payload = {"detector_id": detector, "image_url": image_url}
        if metadata: payload["metadata"] = metadata
        data = _handle(await self._c.post(url, json=payload))
    else:
        files = {"image": ("image.jpg", image_bytes or b"", "application/octet-stream")}
        form = {"detector_id": detector}
        if metadata: form["metadata"] = httpx.JSONEncoder().encode(metadata)
        data = _handle(await self._c.post(url, data=form, files=files))
    return data.get("id") or data.get("image_query_id")

async def get_image_query(self, iq_id: str) -> ImageQuery:
    data = _handle(await self._c.get(f"{self.base}/v1/image-queries/{iq_id}"))
    r = data.get("result") or {}
    return ImageQuery(
        id=data.get("id", iq_id),
        status=("DONE" if data.get("done_processing") else data.get("status", "PROCESSING")),
        result_type=data.get("result_type"),
        done_processing=bool(data.get("done_processing")),
        result=ImageQueryResult(
            label=r.get("label"),
            confidence=r.get("confidence"),
            count=r.get("count") or r.get("value"),
            extra={k:v for k,v in r.items() if k not in {"label","confidence","count","value"}} or None,
        ) if r else None,
    )

async def wait_for_confident_result(self, iq_id: str, threshold: float=0.9, timeout_sec: float=30, poll_interval: float=1.0) -> ImageQuery:
    import asyncio, time as _t
    deadline = _t.time() + timeout_sec
    last: ImageQuery | None = None
    while _t.time() < deadline:
        last = await self.get_image_query(iq_id)
        r = last.result
        if r and r.label and (r.confidence or 0) >= threshold: return last
        if last.done_processing: return last
        await asyncio.sleep(poll_interval)
    return last or await self.get_image_query(iq_id)
class ExperimentalApi:
"""Placeholder for future helpers (rules/webhooks/etc.)."""
def init(self, client: IntelliOptics | AsyncIntelliOptics): self._c = client
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot "src\intellioptics\client.py")

@'
import respx, httpx
from intellioptics import IntelliOptics

@respx.mock
def test_get_image_query_normalizes():
base = "https://api.example.com"; iq_id = "iq_123"
respx.get(f"{base}/v1/image-queries/{iq_id}").mock(
return_value=httpx.Response(200, json={
"id": iq_id, "done_processing": True, "result_type": "YESNO",
"result": {"label": "YES", "confidence": 0.97}
})
)
io = IntelliOptics(endpoint=base, api_token="t")
iq = io.get_image_query(iq_id)
assert iq.done_processing and iq.result.label == "YES"
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot "tests\test_client.py")

@'
pycache/
*.pyc
dist/
build/
*.egg-info/
.venv/
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot ".gitignore")

@'
name: ci
on:
push: { branches: ["main"] }
pull_request:
workflow_dispatch:

jobs:
build:
runs-on: ubuntu-latest
steps:
- uses: actions/checkout@v4
- uses: actions/setup-python@v5
with: { python-version: "3.11" }
- run: python -m pip install -U pip hatch
- run: python -m pip install .[test]
- run: pytest -q
- run: hatch build
'@ | Set-Content -Encoding UTF8 (Join-Path $TempRoot ".github\workflows\ci.yml")
---------- Zip ----------

if (Test-Path $ZipPath) { Remove-Item -Force $ZipPath }
Compress-Archive -Path (Join-Path $TempRoot "*") -DestinationPath $ZipPath -Force

Write-Host "OK: $ZipPath"
Write-Host ""
Write-Host "To extract into C:\Users\ThaMain1\IntelliOptics\intellioptics-python-sdk :"
Write-Host "Expand-Archive -Force "$ZipPath" "$DestRoot\intellioptics-python-sdk""
