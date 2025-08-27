# intellioptics_sdk_bootstrap.ps1
$ErrorActionPreference = "Stop"
$root = "intellioptics-python-sdk"
New-Item -ItemType Directory -Force $root | Out-Null
New-Item -ItemType Directory -Force "$root\src\intellioptics" | Out-Null
New-Item -ItemType Directory -Force "$root\tests" | Out-Null
New-Item -ItemType Directory -Force "$root\.github\workflows" | Out-Null

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
authors = [{ name = "4wardmotions", email = "admin@4wardmotions.com" }]
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
'@ | Set-Content "$root\pyproject.toml"

@'
# IntelliOptics Python SDK

## Quick start
```python
from intellioptics import IntelliOptics

io = IntelliOptics(endpoint="https://YOUR-IO-ENDPOINT", api_token="YOUR_TOKEN")

# submit by URL
iq_id = io.ask_async(detector="det-123", image_url="https://example.com/image.jpg")

# or by local file (if your API supports multipart uploads)
# iq_id = io.ask_async(detector="det-123", image_path="local.jpg")

# wait for result
iq = io.wait_for_confident_result(iq_id, threshold=0.9, timeout_sec=30)
print(iq.status, iq.result)
