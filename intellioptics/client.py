"""High level Python SDK for the IntelliOptics HTTP API."""

from __future__ import annotations

import json
import os
import time
from collections.abc import Mapping
from typing import Any, Dict, IO, Optional, Union

from ._http import HttpClient
from ._img import to_jpeg_bytes
from .errors import ApiTokenError
from .models import Detector, FeedbackIn, ImageQuery, QueryResult, UserIdentity


def _resolve_status(payload: Mapping[str, Any]) -> str:
    """Infer a status value from legacy or partially populated payloads."""

    status = payload.get("status")
    if isinstance(status, str) and status:
        return status

    done_processing = payload.get("done_processing")
    if done_processing is True:
        return "DONE"
    if done_processing is False:
        return "PROCESSING"

    if payload.get("answer") is not None or payload.get("result"):
        return "DONE"

    return "PENDING"


def _normalize_image_query_payload(payload: Mapping[str, Any]) -> Dict[str, Any]:
    """Translate historical payloads into the ImageQuery/QueryResult schema."""

    raw = dict(payload)
    result_block = raw.get("result")
    if not isinstance(result_block, Mapping):
        result_block = {}

    data: Dict[str, Any] = {
        "id": raw.get("id") or raw.get("image_query_id"),
        "detector_id": raw.get("detector_id"),
        "status": _resolve_status(raw),
        "result_type": raw.get("result_type"),
    }

    confidence = raw.get("confidence", result_block.get("confidence"))
    if confidence is not None:
        data["confidence"] = confidence

    label = raw.get("label") or result_block.get("label") or raw.get("answer")
    if label is not None:
        data["label"] = label

    extra: Dict[str, Any] = {}
    raw_extra = raw.get("extra")
    if isinstance(raw_extra, Mapping):
        extra.update(raw_extra)

    for key in ("latency_ms", "model_version", "done_processing"):
        value = raw.get(key)
        if value is not None:
            extra.setdefault(key, value)

    for key, value in result_block.items():
        if key not in {"label", "confidence"} and value is not None:
            extra.setdefault(key, value)

    if extra:
        data["extra"] = extra

    return data


class IntelliOptics:
    """Python SDK that wraps the IntelliOptics HTTP API."""

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_token: Optional[str] = None,
        *,
        disable_tls_verification: Optional[bool] = None,
        timeout: float = 30.0,
    ) -> None:
        endpoint = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT")
        api_token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")

        if not api_token:
            raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")

        verify = not (disable_tls_verification or os.getenv("DISABLE_TLS_VERIFY") == "1")
        self._http = HttpClient(
            base_url=endpoint,
            api_token=api_token,
            verify=verify,
            timeout=timeout,
        )

    # ---------------------------------------------------------------------
    # User helpers
    # ---------------------------------------------------------------------
    def whoami(self) -> UserIdentity:
        """Return the user identity associated with the current token."""

        data = self._http.get_json("/v1/users/me")
        return UserIdentity(**data)

    # ------------------------------------------------------------------
    # Detectors
    # ------------------------------------------------------------------
    def create_detector(
        self,
        name: str,
        mode: str,
        query_text: str,
        threshold: Optional[float] = None,
    ) -> Detector:
        payload: Dict[str, Any] = {
            "name": name,
            "mode": mode,
            "query_text": query_text,
        }
        if threshold is not None:
            payload["threshold"] = threshold

        data = self._http.post_json("/v1/detectors", json=payload)
        return Detector(**data)

    def list_detectors(self) -> list[Detector]:
        payload = self._http.get_json("/v1/detectors")
        items = payload.get("items") if isinstance(payload, Mapping) else payload
        if not isinstance(items, list):
            items = []
        return [Detector(**item) for item in items]

    def get_detector(self, detector_id: str) -> Detector:
        payload = self._http.get_json(f"/v1/detectors/{detector_id}")
        return Detector(**payload)

    # ------------------------------------------------------------------
    # Image queries
    # ------------------------------------------------------------------
    def submit_image_query(
        self,
        detector: Optional[Union[Detector, str]] = None,
        image: Optional[Union[str, bytes, IO[bytes]]] = None,
        *,
        prompt: Optional[str] = None,
        wait: Optional[Union[bool, float]] = None,
        confidence_threshold: Optional[float] = None,
        metadata: Optional[Union[Mapping[str, Any], str]] = None,
        inspection_id: Optional[str] = None,
    ) -> ImageQuery:
        detector_id = detector.id if isinstance(detector, Detector) else detector

        data: Dict[str, Any] = {"detector_id": detector_id, "prompt": prompt, "inspection_id": inspection_id}

        if wait is not None:
            if isinstance(wait, bool):
                data["wait"] = "true" if wait else "false"
            else:
                data["wait"] = wait
        if confidence_threshold is not None:
            data["confidence_threshold"] = confidence_threshold
        if metadata is not None:
            data["metadata"] = json.dumps(metadata) if isinstance(metadata, Mapping) else metadata

        form = {key: value for key, value in data.items() if value is not None}

        files = None
        if image is not None:
            image_bytes = to_jpeg_bytes(image)
            files = {"image": ("image.jpg", image_bytes, "image/jpeg")}

        payload = self._http.post_json("/v1/image-queries", data=form, files=files)
        return ImageQuery(**_normalize_image_query_payload(payload))

    def submit_image_query_json(
        self,
        detector: Optional[Union[Detector, str]] = None,
        *,
        image: Optional[str] = None,
        wait: Optional[bool] = None,
    ) -> ImageQuery:
        detector_id = detector.id if isinstance(detector, Detector) else detector
        payload = {"detector_id": detector_id, "image": image, "wait": wait}
        json_payload = {key: value for key, value in payload.items() if value is not None}
        response = self._http.post_json("/v1/image-queries-json", json=json_payload)
        return ImageQuery(**_normalize_image_query_payload(response))

    def get_image_query(self, image_query_id: str) -> ImageQuery:
        payload = self._http.get_json(f"/v1/image-queries/{image_query_id}")
        return ImageQuery(**_normalize_image_query_payload(payload))

    def get_result(self, image_query_id: str) -> QueryResult:
        payload = self._http.get_json(f"/v1/image-queries/{image_query_id}")
        normalized = _normalize_image_query_payload(payload)
        normalized.pop("detector_id", None)
        return QueryResult(**normalized)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def ask_ml(
        self, detector: Union[Detector, str], image: Union[str, bytes, IO[bytes]], wait: Optional[bool] = None
    ) -> ImageQuery:
        return self.submit_image_query(detector=detector, image=image, wait=wait)

    def ask_confident(
        self,
        detector: Union[Detector, str],
        image: Union[str, bytes, IO[bytes]],
        *,
        confidence_threshold: float = 0.9,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query = self.submit_image_query(detector=detector, image=image)
        return self.wait_for_confident_result(
            query,
            confidence_threshold=confidence_threshold,
            timeout_sec=timeout_sec,
            poll_interval=poll_interval,
        )

    def wait_for_confident_result(
        self,
        image_query: Union[ImageQuery, str],
        *,
        confidence_threshold: float = 0.9,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        deadline = time.time() + timeout_sec

        while True:
            query = self.get_image_query(query_id)
            if query.status in {"DONE", "ERROR"}:
                if query.confidence is None or query.confidence >= confidence_threshold:
                    return query
            if time.time() >= deadline:
                return query
            time.sleep(poll_interval)

    # ------------------------------------------------------------------
    # Labels & feedback
    # ------------------------------------------------------------------
    def add_label(
        self,
        image_query_id: str,
        label: str,
        *,
        confidence: Optional[float] = None,
        detector_id: Optional[str] = None,
        user_id: Optional[str] = None,
        metadata: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload: Dict[str, Any] = {
            "image_query_id": image_query_id,
            "label": label,
            "confidence": confidence,
            "detector_id": detector_id,
            "user_id": user_id,
            "metadata": metadata,
        }
        serialized = {key: value for key, value in payload.items() if value is not None}
        return self._http.post_json("/v1/labels", json=serialized)

    def submit_feedback(
        self,
        feedback: Optional[Union[FeedbackIn, Mapping[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        if feedback is not None and kwargs:
            raise ValueError("Provide feedback as a model/dict or as keyword arguments, not both.")

        if feedback is None:
            feedback_model = FeedbackIn(**kwargs)
        elif isinstance(feedback, FeedbackIn):
            feedback_model = feedback
        else:
            feedback_model = FeedbackIn(**dict(feedback))

        serializer = getattr(feedback_model, "model_dump", None) or getattr(feedback_model, "dict")
        payload = serializer(exclude_none=True) if serializer else dict(feedback_model)
        response = self._http.post_json("/v1/feedback", json=payload)
        return response or {}
