# make_io_sdk_zip.ps1 — creates intellioptics-python-sdk.zip in-place
$ErrorActionPreference = 'Stop'
$DestRoot = 'C:\Users\ThaMain1\IntelliOptics'
$ZipPath  = Join-Path $DestRoot 'intellioptics-python-sdk.zip'

Add-Type -AssemblyName System.IO.Compression, System.IO.Compression.FileSystem

function Add-ZipTextEntry {
  param([System.IO.Compression.ZipArchive]$Zip, [string]$Path, [string]$Text)
  $entry = $Zip.CreateEntry($Path)
  $sw = New-Object System.IO.StreamWriter($entry.Open(), [System.Text.Encoding]::UTF8)
  $sw.NewLine = "`n"
  $sw.Write($Text)
  $sw.Dispose()
}

# ----- file contents (single-quoted strings; safe for backticks) -----
$pyproject = @(
  '[build-system]'
  'requires = ["hatchling>=1.25"]'
  'build-backend = "hatchling.build"'
  ''
  '[project]'
  'name = "intellioptics"'
  'version = "0.1.0"'
  'description = "Official Python SDK for the IntelliOptics API"'
  'readme = "README.md"'
  'requires-python = ">=3.10"'
  'authors = [{ name = "4wardmotions", email = "dev@4wardmotions.com" }]'
  'license = { text = "Proprietary" }'
  'dependencies = ['
  '  "httpx>=0.28.0",'
  '  "pydantic>=2.7.0",'
  '  "typing-extensions>=4.8.0"'
  ']'
  ''
  '[project.optional-dependencies]'
  'test = ["pytest>=7.4", "respx>=0.21.1", "pytest-asyncio>=0.23"]'
  ''
  '[project.urls]'
  'Homepage = "https://4wardmotions.com"'
) -join "`n"

$readme = @(
  '# IntelliOptics Python SDK'
  ''
  '```python'
  'from intellioptics import IntelliOptics'
  ''
  'io = IntelliOptics(endpoint="https://YOUR-ENDPOINT", api_token="YOUR_TOKEN")'
  'iq_id = io.ask_async(detector="det-123", image_url="https://example.com/image.jpg")'
  'iq = io.wait_for_confident_result(iq_id, threshold=0.9, timeout_sec=30)'
  'print(iq.status, iq.result)'
  '```'
  ''
  '## Build'
  '```'
  'python -m pip install -U pip build'
  'python -m build'
  '```'
) -join "`n"

$init_py = @(
  'from .client import IntelliOptics, AsyncIntelliOptics, ExperimentalApi'
  'from .models import ImageQuery, ImageQueryResult'
  'from .exceptions import IntelliOpticsError, ApiError, AuthError, NotFound'
  ''
  '__all__ = ['
  '    "IntelliOptics", "AsyncIntelliOptics", "ExperimentalApi",'
  '    "ImageQuery", "ImageQueryResult",'
  '    "IntelliOpticsError", "ApiError", "AuthError", "NotFound",'
  ']'
  ''
  '__version__ = "0.1.0"'
) -join "`n"

$exceptions_py = @(
  'class IntelliOpticsError(Exception):'
  '    pass'
  ''
  'class AuthError(IntelliOpticsError):'
  '    pass'
  ''
  'class NotFound(IntelliOpticsError):'
  '    pass'
  ''
  'class ApiError(IntelliOpticsError):'
  '    def __init__(self, status: int, message: str, payload=None):'
  '        super().__init__(f"{status}: {message}")'
  '        self.status = status'
  '        self.payload = payload'
) -join "`n"

$models_py = @(
  'from typing import Any, Optional'
  'from pydantic import BaseModel, Field'
  ''
  'class ImageQueryResult(BaseModel):'
  '    label: Optional[str] = None'
  '    confidence: Optional[float] = None'
  '    count: Optional[int] = None'
  '    extra: Optional[dict[str, Any]] = None'
  ''
  'class ImageQuery(BaseModel):'
  '    id: str'
  '    status: str = Field(default="PROCESSING")   # PROCESSING | DONE | FAILED'
  '    result_type: Optional[str] = None'
  '    done_processing: bool = False'
  '    result: Optional[ImageQueryResult] = None'
) -join "`n"

$client_py = @(
  'from __future__ import annotations'
  'import os, time, asyncio, httpx'
  'from typing import Any, Optional'
  'from .exceptions import ApiError, AuthError, NotFound'
  'from .models import ImageQuery, ImageQueryResult'
  ''
  '_DEFAULT_TIMEOUT = float(os.getenv("INTELLIOPTICS_TIMEOUT", "30"))'
  '_UA = "intellioptics-sdk/0.1.0 (+https://4wardmotions.com)"'
  ''
  'def _headers(tok: str|None) -> dict[str,str]:'
  '    h = {"Accept":"application/json","User-Agent":_UA}'
  '    if tok: h["Authorization"]=f"Bearer {tok}"'
  '    return h'
  ''
  'def _handle(r: httpx.Response) -> dict:'
  '    if r.status_code == 401: raise AuthError("Unauthorized")'
  '    if r.status_code == 404: raise NotFound("Resource not found")'
  '    if r.status_code >= 400:'
  '        try: msg = r.json()'
  '        except Exception: msg = r.text'
  '        raise ApiError(r.status_code, str(msg), msg)'
  '    return r.json()'
  ''
  'class IntelliOptics:'
  '    def __init__(self, endpoint: str, api_token: Optional[str]=None, timeout: float=_DEFAULT_TIMEOUT):'
  '        self.base = endpoint.rstrip("/")'
  '        self.token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")'
  '        self._c = httpx.Client(timeout=timeout, headers=_headers(self.token))'
  '    def close(self): self._c.close()'
  ''
  '    def ask_async(self, detector: str, image_url: Optional[str]=None,'
  '                  image_path: Optional[str]=None, image_bytes: Optional[bytes]=None,'
  '                  metadata: Optional[dict[str,Any]]=None) -> str:'
  '        url = f"{self.base}/v1/image-queries"'
  '        if image_url:'
  '            payload = {"detector_id": detector, "image_url": image_url}'
  '            if metadata: payload["metadata"] = metadata'
  '            data = _handle(self._c.post(url, json=payload))'
  '        else:'
  '            if image_path and not image_bytes:'
  '                with open(image_path,"rb") as f: image_bytes = f.read()'
  '            files = {"image": ("image.jpg", image_bytes or b"", "application/octet-stream")}'
  '            form = {"detector_id": detector}'
  '            if metadata: form["metadata"] = httpx.JSONEncoder().encode(metadata)'
  '            data = _handle(self._c.post(url, data=form, files=files))'
  '        return data.get("id") or data.get("image_query_id")'
  ''
  '    def get_image_query(self, iq_id: str) -> ImageQuery:'
  '        d = _handle(self._c.get(f"{self.base}/v1/image-queries/{iq_id}"))'
  '        r = d.get("result") or {}'
  '        return ImageQuery('
  '            id=d.get("id", iq_id),'
  '            status=("DONE" if d.get("done_processing") else d.get("status","PROCESSING")),'
  '            result_type=d.get("result_type"),'
  '            done_processing=bool(d.get("done_processing")),'
  '            result=ImageQueryResult('
  '                label=r.get("label"),'
  '                confidence=r.get("confidence"),'
  '                count=r.get("count") or r.get("value"),'
  '                extra={k:v for k,v in r.items() if k not in {"label","confidence","count","value"}} or None,'
  '            ) if r else None,'
  '        )'
  ''
  '    def wait_for_confident_result(self, iq_id: str, threshold: float=0.9, timeout_sec: float=30, poll_interval: float=1.0) -> ImageQuery:'
  '        deadline = time.time() + timeout_sec; last = None'
  '        while time.time() < deadline:'
  '            last = self.get_image_query(iq_id); r = last.result'
  '            if r and r.label and (r.confidence or 0) >= threshold: return last'
  '            if last.done_processing: return last'
  '            time.sleep(poll_interval)'
  '        return last or self.get_image_query(iq_id)'
  ''
  'class AsyncIntelliOptics:'
  '    def __init__(self, endpoint: str, api_token: Optional[str]=None, timeout: float=_DEFAULT_TIMEOUT):'
  '        self.base = endpoint.rstrip("/")'
  '        self.token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")'
  '        self._c = httpx.AsyncClient(timeout=timeout, headers=_headers(self.token))'
  '    async def aclose(self): await self._c.aclose()'
  ''
  '    async def ask_async(self, detector: str, image_url: Optional[str]=None,'
  '                        image_bytes: Optional[bytes]=None, metadata: Optional[dict[str,Any]]=None) -> str:'
  '        url = f"{self.base}/v1/image-queries"'
  '        if image_url:'
  '            payload = {"detector_id": detector, "image_url": image_url}'
  '            if metadata: payload["metadata"] = metadata'
  '            d = _handle(await self._c.post(url, json=payload))'
  '        else:'
  '            files = {"image": ("image.jpg", image_bytes or b"", "application/octet-stream")}'
  '            form = {"detector_id": detector}'
  '            if metadata: form["metadata"] = httpx.JSONEncoder().encode(metadata)'
  '            d = _handle(await self._c.post(url, data=form, files=files))'
  '        return d.get("id") or d.get("image_query_id")'
  ''
  '    async def get_image_query(self, iq_id: str) -> ImageQuery:'
  '        d = _handle(await self._c.get(f"{self.base}/v1/image-queries/{iq_id}"))'
  '        r = d.get("result") or {}'
  '        return ImageQuery('
  '            id=d.get("id", iq_id),'
  '            status=("DONE" if d.get("done_processing") else d.get("status","PROCESSING")),'
  '            result_type=d.get("result_type"),'
  '            done_processing=bool(d.get("done_processing")),'
  '            result=ImageQueryResult('
  '                label=r.get("label"),'
  '                confidence=r.get("confidence"),'
  '                count=r.get("count") or r.get("value"),'
  '                extra={k:v for k,v in r.items() if k not in {"label","confidence","count","value"}} or None,'
  '            ) if r else None,'
  '        )'
  ''
  '    async def wait_for_confident_result(self, iq_id: str, threshold: float=0.9, timeout_sec: float=30, poll_interval: float=1.0) -> ImageQuery:'
  '        import time as _t; deadline = _t.time() + timeout_sec; last = None'
  '        while _t.time() < deadline:'
  '            last = await self.get_image_query(iq_id); r = last.result'
  '            if r and r.label and (r.confidence or 0) >= threshold: return last'
  '            if last.done_processing: return last'
  '            await asyncio.sleep(poll_interval)'
  '        return last or await self.get_image_query(iq_id)'
  ''
  'class ExperimentalApi:'
  '    def __init__(self, client: IntelliOptics | AsyncIntelliOptics): self._c = client'
) -join "`n"

$test_client_py = @(
  'import respx, httpx'
  'from intellioptics import IntelliOptics'
  ''
  '@respx.mock'
  'def test_get_image_query_normalizes():'
  '    base = "https://api.example.com"; iq_id = "iq_123"'
  '    respx.get(f"{base}/v1/image-queries/{iq_id}").mock('
  '        return_value=httpx.Response(200, json={'
  '            "id": iq_id, "done_processing": True, "result_type": "YESNO",'
  '            "result": {"label": "YES", "confidence": 0.97}'
  '        })'
  '    )'
  '    io = IntelliOptics(endpoint=base, api_token="t")'
  '    iq = io.get_image_query(iq_id)'
  '    assert iq.done_processing and iq.result.label == "YES"'
) -join "`n"

$gitignore = @(
  '__pycache__/'
  '*.pyc'
  'dist/'
  'build/'
  '*.egg-info/'
  '.venv/'
) -join "`n"

$ci_yml = @(
  'name: ci'
  'on:'
  '  push: { branches: ["main"] }'
  '  pull_request:'
  '  workflow_dispatch:'
  ''
  'jobs:'
  '  build:'
  '    runs-on: ubuntu-latest'
  '    steps:'
  '      - uses: actions/checkout@v4'
  '      - uses: actions/setup-python@v5'
  '        with: { python-version: "3.11" }'
  '      - run: python -m pip install -U pip hatch'
  '      - run: python -m pip install .[test]'
  '      - run: pytest -q'
  '      - run: hatch build'
) -join "`n"

# fresh zip
if (Test-Path $ZipPath) { Remove-Item $ZipPath -Force }
$fs  = [System.IO.File]::Open($ZipPath, [System.IO.FileMode]::Create, [System.IO.FileAccess]::Write, [System.IO.FileShare]::None)
$zip = New-Object System.IO.Compression.ZipArchive($fs, [System.IO.Compression.ZipArchiveMode]::Create, $false)

Add-ZipTextEntry $zip 'pyproject.toml'                       $pyproject
Add-ZipTextEntry $zip 'README.md'                            $readme
Add-ZipTextEntry $zip 'src/intellioptics/__init__.py'        $init_py
Add-ZipTextEntry $zip 'src/intellioptics/exceptions.py'      $exceptions_py
Add-ZipTextEntry $zip 'src/intellioptics/models.py'          $models_py
Add-ZipTextEntry $zip 'src/intellioptics/client.py'          $client_py
Add-ZipTextEntry $zip 'tests/test_client.py'                 $test_client_py
Add-ZipTextEntry $zip '.gitignore'                           $gitignore
Add-ZipTextEntry $zip '.github/workflows/ci.yml'             $ci_yml

$zip.Dispose(); $fs.Dispose()
Write-Host "ZIP ready: $ZipPath"
Get-Item $ZipPath | Select-Object FullName, Length, LastWriteTime | Format-List