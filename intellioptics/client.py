import json
import os, time
import json
import json
import os
import time
from typing import Optional, Union, IO, List

import os, time
from typing import Optional, Union, IO, List, Dict, Any
from .errors import ApiTokenError
from .models import Detector, ImageQuery, QueryResult, UserIdentity, FeedbackIn
from .models import Detector, ImageQuery, QueryResult, FeedbackIn
from .models import Detector, ImageQuery, QueryResult, UserIdentity
from ._http import HttpClient


def _normalize_image_query_payload(payload: dict) -> dict:
    """Translate legacy answer payloads into the ImageQuery/QueryResult schema."""

    if not isinstance(payload, dict):
        return payload

    # If the payload already looks like an ImageQuery, return as-is.
    if "id" in payload and ("status" in payload or "label" in payload):
        return payload

    image_query_id = payload.get("image_query_id") or payload.get("id")
    if not image_query_id:
        return payload

    status = payload.get("status")
    if not status:
        # Fall back to a best-effort default. Legacy responses only contained
        # the answer when the inference completed, so we treat it as DONE.
        status = "DONE" if payload.get("answer") is not None else "PENDING"

    normalized = {
        "id": image_query_id,
        "detector_id": payload.get("detector_id"),
        "status": status,
        "result_type": payload.get("result_type"),
        "confidence": payload.get("confidence"),
        "label": payload.get("label") or payload.get("answer"),
        "extra": payload.get("extra"),
    }

    # Strip keys with None values except for required ones.
    return {k: v for k, v in normalized.items() if v is not None or k in {"id", "status"}}
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
    def create_detector(
        self,
        name: str,
        mode: str,
        query_text: str,
        threshold: Optional[float] = None,
    ) -> Detector:
        payload = {
            "name": name,
            "mode": mode,
            "query_text": query_text,
        }
        if threshold is not None:
            payload["threshold"] = threshold
        data = self._http.post_json("/v1/detectors", json=payload)
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

                           confidence_threshold: Optional[float] = None,
                           metadata: Optional[Union[Dict[str, Any], str]] = None,

                           confidence_threshold: Optional[float] = None, metadata: Optional[Dict[str, Any]] = None,

                           inspection_id: Optional[str] = None) -> ImageQuery:

    def submit_image_query(
        self,
        detector: Optional[Union[Detector, str]] = None,
        image: Optional[Union[str, bytes, IO[bytes]]] = None,
        wait: Optional[bool] = None,
    ) -> ImageQuery:
        detector_id = detector.id if isinstance(detector, Detector) else detector
        form = {"detector_id": detector_id}
        if wait is not None:
            form["wait"] = "true" if wait else "false"


        img = to_jpeg_bytes(image) if image is not None else None
        files = {"image": ("image.jpg", img, "image/jpeg")} if img else None
        form = {
            "detector_id": detector.id if isinstance(detector, Detector) else detector,
            "prompt": prompt,
            "wait": wait,
            "confidence_threshold": confidence_threshold,
            "metadata": metadata,
            "inspection_id": inspection_id,
            "metadata": json.dumps(metadata) if metadata is not None else None,
        }

        if metadata is not None:
            form["metadata"] = json.dumps(metadata)

        if metadata is not None:
            form["metadata"] = json.dumps(metadata) if isinstance(metadata, dict) else metadata

        if metadata is not None:
            form["metadata"] = json.dumps(metadata) if isinstance(metadata, dict) else metadata

        if metadata is not None:
            form["metadata"] = json.dumps(metadata)


        form = {k: v for k, v in form.items() if v is not None}

        if "metadata" in form and not isinstance(form["metadata"], str):
            form["metadata"] = json.dumps(form["metadata"])


        payload = self._http.post_json("/v1/image-queries", files=files, data=form)
        return ImageQuery(**_normalize_image_query_payload(payload))
        return ImageQuery(**self._http.post_json("/v1/image-queries", files=files, data=form))
    def submit_image_query(self, detector: Optional[Union[Detector, str]] = None,
                           image: Optional[Union[str, bytes, IO[bytes]]] = None,
                           wait: Optional[bool] = None) -> ImageQuery:
        img = to_jpeg_bytes(image) if image is not None else None
        files = {"image": ("image.jpg", img, "image/jpeg")} if img is not None else None

        detector_id = None
        if isinstance(detector, Detector):
            detector_id = detector.id
        elif detector is not None:
            detector_id = str(detector)

        form = {}
        if detector_id is not None:
            form["detector_id"] = detector_id
        if wait is not None:
            form["wait"] = "true" if wait else "false"

        post_kwargs = {"data": form}
        if files is not None:
            post_kwargs["files"] = files

        return ImageQuery(**self._http.post_json("/v1/image-queries", **post_kwargs))

    def submit_image_query_json(self, detector: Optional[Union[Detector, str]] = None,
                                image: Optional[str] = None,
                                wait: Optional[bool] = None) -> ImageQuery:
        detector_id = None
        if isinstance(detector, Detector):
            detector_id = detector.id
        elif detector is not None:
            detector_id = str(detector)

        payload = {}
        if detector_id is not None:
            payload["detector_id"] = detector_id
        if image is not None:
            payload["image"] = image
        if wait is not None:
            payload["wait"] = wait

        return ImageQuery(**self._http.post_json("/v1/image-queries-json", json=payload))

    def submit_image_query_json(
        self,
        detector: Optional[Union[Detector, str]] = None,
        image_base64: Optional[str] = None,
        wait: Optional[bool] = None,
    ) -> ImageQuery:
        detector_id = detector.id if isinstance(detector, Detector) else detector
        payload = {"detector_id": detector_id, "image": image_base64, "wait": wait}
        payload = {k: v for k, v in payload.items() if v is not None}
        return ImageQuery(**self._http.post_json("/v1/image-queries-json", json=payload))


    def get_image_query(self, image_query_id: str) -> ImageQuery:
        payload = self._http.get_json(f"/v1/image-queries/{image_query_id}")
        return ImageQuery(**_normalize_image_query_payload(payload))

    def get_result(self, image_query_id: str) -> QueryResult:
        payload = self._http.get_json(f"/v1/image-queries/{image_query_id}")
        normalized = _normalize_image_query_payload(payload)
        normalized.pop("detector_id", None)
        return QueryResult(**normalized)

    # Helpers similar to GL
    def ask_ml(self, detector: Union[Detector, str], image, wait: Optional[bool] = None) -> ImageQuery:
        return self.submit_image_query(detector=detector, image=image, wait=wait)

    def ask_confident(self, detector: Union[Detector, str], image, confidence_threshold: float = 0.9,
                      timeout_sec: float = 30.0, poll_interval: float = 0.5) -> ImageQuery:
        iq = self.submit_image_query(detector=detector, image=image)
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

    def submit_feedback(self, feedback: FeedbackIn | None = None, **kwargs) -> dict:
        """Submit feedback for an image query.

        Either supply a :class:`FeedbackIn` instance or the required keyword arguments
        (``image_query_id`` and ``correct_label`` with optional ``bboxes`` and other
        fields accepted by the model).
        """

        if feedback is not None and kwargs:
            raise TypeError("submit_feedback accepts either a FeedbackIn instance or keyword arguments, not both")

        if feedback is None:
            feedback = FeedbackIn(**kwargs)
        elif not isinstance(feedback, FeedbackIn):
            feedback = FeedbackIn(**feedback)

        serializer = getattr(feedback, "model_dump", feedback.dict)
        payload = serializer(exclude_none=True)
        try:
            response = self._http.post_json("/v1/feedback", json=payload)
        except ValueError:
            return {}
        return response or {}
    def submit_feedback(self, feedback: Optional[Union[FeedbackIn, Dict[str, Any]]] = None,
                        **kwargs) -> Dict[str, Any]:
        if feedback is not None and kwargs:
            raise ValueError("Provide feedback as a model/dict or as keyword arguments, not both.")

        if feedback is None:
            feedback_model = FeedbackIn(**kwargs)
        elif isinstance(feedback, FeedbackIn):
            feedback_model = feedback
        else:
            feedback_model = FeedbackIn(**feedback)

        if hasattr(feedback_model, "model_dump"):
            payload = feedback_model.model_dump(exclude_none=True)
        else:
            payload = feedback_model.dict(exclude_none=True)
        return self._http.post_json("/v1/feedback", json=payload)
