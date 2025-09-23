import os
from typing import Any, Dict, List, Optional

import httpx

from .exceptions import ApiError, AuthError
from .types import Answer, Detector

DEFAULT_BASE_URL = os.getenv("INTELLOPTICS_BASE_URL", "https://api.intellioptics.co")
DEFAULT_TOKEN = os.getenv("INTELLOPTICS_API_TOKEN")


class IntelliOptics:
    """Groundlight-style client with familiar method names."""

    def __init__(self, api_token: Optional[str] = None, base_url: str = DEFAULT_BASE_URL, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_token = api_token or DEFAULT_TOKEN
        if not self.api_token:
            raise AuthError("Missing API token. Set INTELLOPTICS_API_TOKEN or pass api_token=...")
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_token}"},
            timeout=timeout,
        )

    # --- Detectors ---
    def create_detector(self, name: str, labels: Optional[List[str]] = None, **extra_fields: Any) -> Detector:
        payload: Dict[str, Any] = {"name": name}
        if labels is not None:
            payload["labels"] = labels
        if extra_fields:
            payload.update(extra_fields)
        r = self._client.post("/v1/detectors", json=payload)
        _ok(r)
        return _to_detector(r.json())

    def list_detectors(self) -> List[Detector]:
        r = self._client.get("/v1/detectors")
        _ok(r)
        data = r.json()
        items = data.get("items", data if isinstance(data, list) else [])
        return [_to_detector(item) for item in items]

    def get_detector(self, detector_id: str) -> Detector:
        r = self._client.get(f"/v1/detectors/{detector_id}")
        _ok(r)
        return _to_detector(r.json())

    # --- Image Queries / Answers ---
    def ask_image(self, detector_id: str, image: bytes | str, wait: bool = True) -> Answer:
        """
        image: bytes OR local path/URL string. If bytes or local file, send multipart; else JSON with URL.
        """
        if isinstance(image, str) and os.path.exists(image):
            with open(image, "rb") as f:
                img_bytes = f.read()
            files = {"image": img_bytes}
            data = {"detector_id": detector_id, "wait": wait}
            r = self._client.post("/v1/image-queries", data=data, files=files)
        elif isinstance(image, (bytes, bytearray)):
            files = {"image": bytes(image)}
            data = {"detector_id": detector_id, "wait": wait}
            r = self._client.post("/v1/image-queries", data=data, files=files)
        else:
            # assume it's a URL
            payload = {"detector_id": detector_id, "image": image, "wait": wait}
            r = self._client.post("/v1/image-queries", json=payload)
        _ok(r)
        j = r.json()
        return Answer(
            answer=j["answer"],
            confidence=j["confidence"],
            id=j["image_query_id"],
            latency_ms=j.get("latency_ms"),
            model_version=j.get("model_version"),
        )

    def get_answer(self, image_query_id: str) -> Answer:
        r = self._client.get(f"/v1/image-queries/{image_query_id}")
        _ok(r)
        j = r.json()
        return Answer(
            answer=j["answer"],
            confidence=j["confidence"],
            id=j["id"],
            latency_ms=j.get("latency_ms"),
            model_version=j.get("model_version"),
        )

    # --- Feedback ---
    def send_feedback(self, image_query_id: str, correct_label: str, bboxes: list[dict] | None = None) -> Dict[str, Any]:
        payload = {"image_query_id": image_query_id, "correct_label": correct_label}
        if bboxes:
            payload["bboxes"] = bboxes
        r = self._client.post("/v1/feedback", json=payload)
        _ok(r)
        return r.json()


def _ok(r: httpx.Response) -> None:
    if 200 <= r.status_code < 300:
        return
    if r.status_code in (401, 403):
        raise AuthError(f"Auth failed: {r.text}")
    raise ApiError(f"{r.status_code}: {r.text}")


def _to_detector(data: Dict[str, Any]) -> Detector:
    labels = data.get("labels") or []
    known = {"id", "name", "labels", "status", "created_at", "updated_at", "metadata"}
    extra = {k: v for k, v in data.items() if k not in known}
    return Detector(
        id=data["id"],
        name=data["name"],
        labels=list(labels),
        status=data.get("status", "active"),
        created_at=data.get("created_at"),
        updated_at=data.get("updated_at"),
        metadata=data.get("metadata"),
        extra=extra,
    )
