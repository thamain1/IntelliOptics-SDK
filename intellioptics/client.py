import json
import os
import time
from typing import Optional, Union, IO, List
from .errors import ApiTokenError
from .models import Detector, ImageQuery, QueryResult, UserIdentity
from ._http import HttpClient
from ._img import to_jpeg_bytes

class IntelliOptics:
    def __init__(self, endpoint: Optional[str] = None, api_token: Optional[str] = None,
                 disable_tls_verification: Optional[bool] = None, timeout: float = 30.0):
        endpoint = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT")
        api_token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
        if not api_token:
            raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")
        self._http = HttpClient(
            base_url=endpoint,
            api_token=api_token,
            verify=not (disable_tls_verification or os.getenv("DISABLE_TLS_VERIFY") == "1"),
            timeout=timeout,
        )

    # Basic health
    def whoami(self) -> UserIdentity:
        data = self._http.get_json("/v1/users/me")
        return UserIdentity(**data)

    # Detectors
    def create_detector(self, name: str, labels: Optional[List[str]] = None) -> Detector:
        data = self._http.post_json("/v1/detectors", json={"name": name, "labels": labels or []})
        return Detector(**data)

    def list_detectors(self) -> List[Detector]:
        data = self._http.get_json("/v1/detectors")
        items = data.get("items", data if isinstance(data, list) else [])
        return [Detector(**d) for d in items]

    def get_detector(self, detector_id: str) -> Detector:
        return Detector(**self._http.get_json(f"/v1/detectors/{detector_id}"))

    # Image queries
    def submit_image_query(self, detector: Optional[Union[Detector, str]] = None, image: Optional[Union[str, bytes, IO[bytes]]] = None,
                           prompt: Optional[str] = None, wait: Optional[float] = None,
                           confidence_threshold: Optional[float] = None, metadata: Optional[dict] = None,
                           inspection_id: Optional[str] = None) -> ImageQuery:
        img = to_jpeg_bytes(image) if image is not None else None
        files = {"image": ("image.jpg", img, "image/jpeg")} if img else None
        form = {
            "detector_id": detector.id if isinstance(detector, Detector) else detector,
            "prompt": prompt,
            "wait": wait,
            "confidence_threshold": confidence_threshold,
            "inspection_id": inspection_id,
            "metadata": json.dumps(metadata) if metadata is not None else None,
        }
        form = {k: v for k, v in form.items() if v is not None}
        return ImageQuery(**self._http.post_json("/v1/image-queries", files=files, data=form))

    def get_image_query(self, image_query_id: str) -> ImageQuery:
        return ImageQuery(**self._http.get_json(f"/v1/image-queries/{image_query_id}"))

    def get_result(self, image_query_id: str) -> QueryResult:
        return QueryResult(**self._http.get_json(f"/v1/image-queries/{image_query_id}"))

    # Helpers similar to GL
    def ask_ml(self, detector: Union[Detector, str], image, wait: Optional[float] = 0.0) -> ImageQuery:
        return self.submit_image_query(detector=detector, image=image, wait=wait)

    def ask_confident(self, detector: Union[Detector, str], image, confidence_threshold: float = 0.9,
                      timeout_sec: float = 30.0, poll_interval: float = 0.5) -> ImageQuery:
        iq = self.submit_image_query(detector=detector, image=image, confidence_threshold=confidence_threshold)
        return self.wait_for_confident_result(iq, confidence_threshold, timeout_sec, poll_interval)

    def wait_for_confident_result(self, image_query: Union[ImageQuery, str], confidence_threshold: float = 0.9,
                                  timeout_sec: float = 30.0, poll_interval: float = 0.5) -> ImageQuery:
        iq_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        start = time.time()
        while True:
            iq = self.get_image_query(iq_id)
            if iq.status in ("DONE", "ERROR"):
                if iq.confidence is None or iq.confidence >= confidence_threshold:
                    return iq
            if time.time() - start > timeout_sec:
                return iq
            time.sleep(poll_interval)

    # Labels
    def add_label(self, image_query_id: str, label: str,
                  confidence: float | None = None,
                  detector_id: str | None = None,
                  user_id: str | None = None,
                  metadata: dict | None = None) -> dict:
        payload = {
            "image_query_id": image_query_id,
            "label": label,
            "confidence": confidence,
            "detector_id": detector_id,
            "user_id": user_id,
            "metadata": metadata,
        }
        # strip None values
        payload = {k: v for k, v in payload.items() if v is not None}
        return self._http.post_json("/v1/labels", json=payload)
