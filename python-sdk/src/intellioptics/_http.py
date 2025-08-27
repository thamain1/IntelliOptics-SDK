from __future__ import annotations
import httpx
from typing import Any

def make_httpx_client(*, base_url: str, verify: bool, timeout: Any) -> httpx.Client:
    # Keep default headers minimal; user-agent helps server logs
    headers = {"User-Agent": "intellioptics-sdk"}
    return httpx.Client(base_url=base_url, verify=verify, timeout=timeout, headers=headers)
