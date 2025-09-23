from __future__ import annotations

import json
import os
import time
from os import PathLike
from typing import Any, Dict, Iterable, Optional, Sequence, Union

from ._http import HttpClient
from ._img import to_jpeg_bytes
from .errors import ApiTokenError
from .models import (
    Answer,
    AnswerLabel,
    DetectorCreate,
    DetectorMode,
    DetectorOut,
    FeedbackIn,
    ImageQueryJson,
)

DetectorLike = Union[str, DetectorOut]
AnswerLike = Union[str, Answer]
ImageType = Union[str, bytes, PathLike[str], Any]


def _dump_model(model: Any, **kwargs: Any) -> Dict[str, Any]:
    if hasattr(model, "to_dict"):
        return model.to_dict(**kwargs)
    if hasattr(model, "model_dump"):
        return model.model_dump(**kwargs)
    return model.dict(**kwargs)


def _parse_model(model_cls: Any, data: Any) -> Any:
    if hasattr(model_cls, "parse"):
        return model_cls.parse(data)
    if hasattr(model_cls, "model_validate"):
        return model_cls.model_validate(data)
    return model_cls.parse_obj(data)


class IntelliOptics:
    """High-level IntelliOptics SDK client."""

    def __init__(
        self,
        *,
        endpoint: Optional[str] = None,
        api_token: Optional[str] = None,
        disable_tls_verification: Optional[bool] = None,
        timeout: float = 30.0,
    ) -> None:
        token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
        if not token:
            raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")

        base_url = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT") or "http://localhost:8000"
        disable_env = os.getenv("DISABLE_TLS_VERIFY") == "1"
        verify = not ((disable_tls_verification is True) or disable_env)

        self._http = HttpClient(
            base_url=base_url,
            api_token=token,
            verify=verify,
            timeout=timeout,
        )
        self.base_url = base_url
        self.api_token = token

    # ---- Detector operations ----
    def create_detector(
        self,
        *,
        name: str,
        mode: Union[DetectorMode, str],
        query_text: str,
        threshold: Optional[float] = None,
    ) -> DetectorOut:
        create_kwargs: Dict[str, Any] = {
            "name": name,
            "mode": DetectorMode(mode),
            "query_text": query_text,
        }
        if threshold is not None:
            create_kwargs["threshold"] = threshold
        payload = DetectorCreate(**create_kwargs)
        data = self._http.post_json("/v1/detectors", json=_dump_model(payload, by_alias=True, exclude_none=True))
        return _parse_model(DetectorOut, data)

    def get_detector(self, detector_id: str) -> DetectorOut:
        data = self._http.get_json(f"/v1/detectors/{detector_id}")
        return _parse_model(DetectorOut, data)

    def list_detectors(self) -> Sequence[DetectorOut]:
        data = self._http.get_json("/v1/detectors")
        if data is None:
            return []
        if isinstance(data, dict) and "items" in data:
            items = data.get("items", [])
        else:
            items = data
        return [_parse_model(DetectorOut, item) for item in items or []]

    # ---- Query submission ----
    def ask_image(
        self,
        detector: DetectorLike,
        image: ImageType,
        *,
        wait: bool = False,
        confidence_threshold: Optional[float] = None,
        human_review: Optional[str] = None,
        metadata: Optional[Union[Dict[str, Any], str]] = None,
        inspection_id: Optional[str] = None,
    ) -> Answer:
        detector_id = detector.id if isinstance(detector, DetectorOut) else str(detector)
        jpg = to_jpeg_bytes(image)
        files = {"image": ("image.jpg", jpg, "image/jpeg")}
        data: Dict[str, Any] = {"detector_id": detector_id}
        data["wait"] = "true" if wait else "false"
        if confidence_threshold is not None:
            data["confidence_threshold"] = str(confidence_threshold)
        if human_review is not None:
            data["human_review"] = human_review
        if metadata is not None:
            data["metadata"] = json.dumps(metadata) if isinstance(metadata, dict) else str(metadata)
        if inspection_id is not None:
            data["inspection_id"] = inspection_id

        result = self._http.post_json("/v1/image-queries", data=data, files=files)
        return _parse_model(Answer, result)

    def ask_ml(
        self,
        detector: DetectorLike,
        *,
        image: Optional[str] = None,
        wait: bool = False,
    ) -> Answer:
        detector_id = detector.id if isinstance(detector, DetectorOut) else str(detector)
        payload = ImageQueryJson(detector_id=detector_id, image=image, wait=wait)
        result = self._http.post_json("/v1/image-queries-json", json=_dump_model(payload, by_alias=True, exclude_none=True))
        return _parse_model(Answer, result)

    def ask_confident(
        self,
        detector: DetectorLike,
        image: ImageType,
        *,
        confidence_threshold: float = 0.9,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
        human_review: Optional[str] = None,
        metadata: Optional[Union[Dict[str, Any], str]] = None,
        inspection_id: Optional[str] = None,
    ) -> Answer:
        initial = self.ask_image(
            detector,
            image,
            wait=False,
            confidence_threshold=confidence_threshold,
            human_review=human_review,
            metadata=metadata,
            inspection_id=inspection_id,
        )
        if initial.confidence >= confidence_threshold:
            return initial
        return self.wait_for_confident_result(
            initial,
            confidence_threshold=confidence_threshold,
            timeout_sec=timeout_sec,
            poll_interval=poll_interval,
        )

    # ---- Result helpers ----
    def get_answer(self, image_query: AnswerLike) -> Answer:
        iq_id = (
            image_query.image_query_id
            if isinstance(image_query, Answer)
            else str(image_query)
        )
        data = self._http.get_json(f"/v1/image-queries/{iq_id}")
        return _parse_model(Answer, data)

    def wait_for_confident_result(
        self,
        image_query: AnswerLike,
        *,
        confidence_threshold: float = 0.9,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> Answer:
        iq_id = (
            image_query.image_query_id
            if isinstance(image_query, Answer)
            else str(image_query)
        )
        start = time.time()
        latest = self.get_answer(iq_id)
        while latest.confidence < confidence_threshold and (time.time() - start) < timeout_sec:
            time.sleep(poll_interval)
            latest = self.get_answer(iq_id)
        return latest

    def send_feedback(
        self,
        *,
        image_query_id: str,
        correct_label: Union[AnswerLabel, str],
        bboxes: Optional[Iterable[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        payload = FeedbackIn(
            image_query_id=image_query_id,
            correct_label=AnswerLabel(correct_label),
            bboxes=list(bboxes) if bboxes is not None else None,
        )
        return self._http.post_json("/v1/feedback", json=_dump_model(payload, by_alias=True, exclude_none=True))

    # ---- Misc helpers ----
    def whoami(self) -> Dict[str, Any]:
        """Return the identity of the authenticated user."""
        return self._http.get_json("/v1/users/me")

    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "IntelliOptics":  # pragma: no cover - convenience helper
        return self

    def __exit__(self, *exc: Any) -> None:  # pragma: no cover - convenience helper
        self.close()
