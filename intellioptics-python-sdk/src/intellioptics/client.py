from __future__ import annotations
import os, time, asyncio, httpx
from typing import Any, Optional
from .exceptions import ApiError, AuthError, NotFound
from .models import ImageQuery, ImageQueryResult

_DEFAULT_TIMEOUT = float(os.getenv("INTELLIOPTICS_TIMEOUT", "30"))
_UA = "intellioptics-sdk/0.1.0 (+https://4wardmotions.com)"

def _headers(tok: str|None) -> dict[str,str]:
    h = {"Accept":"application/json","User-Agent":_UA}
    if tok: h["Authorization"]=f"Bearer {tok}"
    return h

def _handle(r: httpx.Response) -> dict:
    if r.status_code == 401: raise AuthError("Unauthorized")
    if r.status_code == 404: raise NotFound("Resource not found")
    if r.status_code >= 400:
        try: msg = r.json()
        except Exception: msg = r.text
        raise ApiError(r.status_code, str(msg), msg)
    return r.json()

class IntelliOptics:
    def __init__(self, endpoint: str, api_token: Optional[str]=None, timeout: float=_DEFAULT_TIMEOUT):
        self.base = endpoint.rstrip("/")
        self.token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
        self._c = httpx.Client(timeout=timeout, headers=_headers(self.token))
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
                with open(image_path,"rb") as f: image_bytes = f.read()
            files = {"image": ("image.jpg", image_bytes or b"", "application/octet-stream")}
            form = {"detector_id": detector}
            if metadata: form["metadata"] = httpx.JSONEncoder().encode(metadata)
            data = _handle(self._c.post(url, data=form, files=files))
        return data.get("id") or data.get("image_query_id")

    def get_image_query(self, iq_id: str) -> ImageQuery:
        d = _handle(self._c.get(f"{self.base}/v1/image-queries/{iq_id}"))
        r = d.get("result") or {}
        return ImageQuery(
            id=d.get("id", iq_id),
            status=("DONE" if d.get("done_processing") else d.get("status","PROCESSING")),
            result_type=d.get("result_type"),
            done_processing=bool(d.get("done_processing")),
            result=ImageQueryResult(
                label=r.get("label"),
                confidence=r.get("confidence"),
                count=r.get("count") or r.get("value"),
                extra={k:v for k,v in r.items() if k not in {"label","confidence","count","value"}} or None,
            ) if r else None,
        )

    def wait_for_confident_result(self, iq_id: str, threshold: float=0.9, timeout_sec: float=30, poll_interval: float=1.0) -> ImageQuery:
        deadline = time.time() + timeout_sec; last = None
        while time.time() < deadline:
            last = self.get_image_query(iq_id); r = last.result
            if r and r.label and (r.confidence or 0) >= threshold: return last
            if last.done_processing: return last
            time.sleep(poll_interval)
        return last or self.get_image_query(iq_id)

class AsyncIntelliOptics:
    def __init__(self, endpoint: str, api_token: Optional[str]=None, timeout: float=_DEFAULT_TIMEOUT):
        self.base = endpoint.rstrip("/")
        self.token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
        self._c = httpx.AsyncClient(timeout=timeout, headers=_headers(self.token))
    async def aclose(self): await self._c.aclose()

    async def ask_async(self, detector: str, image_url: Optional[str]=None,
                        image_bytes: Optional[bytes]=None, metadata: Optional[dict[str,Any]]=None) -> str:
        url = f"{self.base}/v1/image-queries"
        if image_url:
            payload = {"detector_id": detector, "image_url": image_url}
            if metadata: payload["metadata"] = metadata
            d = _handle(await self._c.post(url, json=payload))
        else:
            files = {"image": ("image.jpg", image_bytes or b"", "application/octet-stream")}
            form = {"detector_id": detector}
            if metadata: form["metadata"] = httpx.JSONEncoder().encode(metadata)
            d = _handle(await self._c.post(url, data=form, files=files))
        return d.get("id") or d.get("image_query_id")

    async def get_image_query(self, iq_id: str) -> ImageQuery:
        d = _handle(await self._c.get(f"{self.base}/v1/image-queries/{iq_id}"))
        r = d.get("result") or {}
        return ImageQuery(
            id=d.get("id", iq_id),
            status=("DONE" if d.get("done_processing") else d.get("status","PROCESSING")),
            result_type=d.get("result_type"),
            done_processing=bool(d.get("done_processing")),
            result=ImageQueryResult(
                label=r.get("label"),
                confidence=r.get("confidence"),
                count=r.get("count") or r.get("value"),
                extra={k:v for k,v in r.items() if k not in {"label","confidence","count","value"}} or None,
            ) if r else None,
        )

    async def wait_for_confident_result(self, iq_id: str, threshold: float=0.9, timeout_sec: float=30, poll_interval: float=1.0) -> ImageQuery:
        import time as _t; deadline = _t.time() + timeout_sec; last = None
        while _t.time() < deadline:
            last = await self.get_image_query(iq_id); r = last.result
            if r and r.label and (r.confidence or 0) >= threshold: return last
            if last.done_processing: return last
            await asyncio.sleep(poll_interval)
        return last or await self.get_image_query(iq_id)

class ExperimentalApi:
    def __init__(self, client: IntelliOptics | AsyncIntelliOptics): self._c = client
