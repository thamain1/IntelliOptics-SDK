# intellioptics_sdk_zip.ps1
$ErrorActionPreference = "Stop"

# Paths
$DestRoot = 'C:\Users\ThaMain1\IntelliOptics'
$SDK      = Join-Path $DestRoot 'intellioptics-python-sdk'
$ZipPath  = Join-Path $DestRoot 'intellioptics-python-sdk.zip'

# Fresh SDK tree
New-Item -ItemType Directory -Force $SDK, "$SDK\src\intellioptics", "$SDK\tests", "$SDK\.github\workflows" | Out-Null

# ---------------- Files ----------------
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
'@ | Set-Content -Encoding UTF8 "$SDK\pyproject.toml"

@'
# IntelliOptics Python SDK

```python
from intellioptics import IntelliOptics

io = IntelliOptics(endpoint="https://YOUR-ENDPOINT", api_token="YOUR_TOKEN")
iq_id = io.ask_async(detector="det-123", image_url="https://example.com/image.jpg")
iq = io.wait_for_confident_result(iq_id, threshold=0.9, timeout_sec=30)
print(iq.status, iq.result)
