"""High level Python SDK for the IntelliOptics HTTP API."""

from __future__ import annotations

from __future__ import annotations

import asyncio
import json
import os
import time
from collections.abc import Mapping
from typing import Any, Dict, IO, Iterable, Optional, Union

from ._http import AsyncHttpClient, HttpClient
from ._img import to_jpeg_bytes
from .errors import ApiTokenError, ExperimentalFeatureUnavailable, IntelliOpticsClientError
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


def _coerce_image_query_items(payload: Any) -> list[Mapping[str, Any]]:
    """Best-effort extraction of image query collections from heterogeneous payloads."""

    if isinstance(payload, Mapping):
        for key in ("items", "results", "data", "image_queries"):
            items = payload.get(key)
            if isinstance(items, Iterable):
                return [item for item in items if isinstance(item, Mapping)]
        if payload.get("id") and payload.get("status"):
            return [payload]
        return []

    if isinstance(payload, Iterable):
        return [item for item in payload if isinstance(item, Mapping)]

    return []


def _build_image_query_request(
    detector: Optional[Union[Detector, str]],
    image: Optional[Union[str, bytes, IO[bytes]]],
    *,
    prompt: Optional[str],
    wait: Optional[Union[bool, float]],
    confidence_threshold: Optional[float],
    metadata: Optional[Union[Mapping[str, Any], str]],
    inspection_id: Optional[str],
) -> tuple[Dict[str, Any], Dict[str, Any] | None]:
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

    return form, files


def _prepare_feedback_payload(
    feedback: Optional[Union[FeedbackIn, Mapping[str, Any]]],
    kwargs: Mapping[str, Any],
) -> Dict[str, Any]:
    if feedback is not None and kwargs:
        raise ValueError("Provide feedback as a model/dict or as keyword arguments, not both.")

    if feedback is None:
        feedback_model = FeedbackIn(**dict(kwargs))
    elif isinstance(feedback, FeedbackIn):
        feedback_model = feedback
    else:
        feedback_model = FeedbackIn(**dict(feedback))

    serializer = getattr(feedback_model, "model_dump", None) or getattr(feedback_model, "dict", None)
    if serializer is not None:
        payload = serializer(exclude_none=True)
    else:  # pragma: no cover - defensive fallback for exotic models
        payload = dict(feedback_model)

    return payload


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
        self.experimental = ExperimentalApi(sync_client=self)

    def close(self) -> None:
        """Close the underlying HTTP session."""

        self._http.close()

    def __enter__(self) -> "IntelliOptics":  # pragma: no cover - trivial context manager
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial context manager
        self.close()

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
        form, files = _build_image_query_request(
            detector,
            image,
            prompt=prompt,
            wait=wait,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
        )

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

    def list_image_queries(
        self,
        *,
        detector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[ImageQuery]:
        params = {
            "detector_id": detector_id,
            "status": status,
            "limit": limit,
            "cursor": cursor,
        }
        params = {key: value for key, value in params.items() if value is not None}
        payload = self._http.get_json("/v1/image-queries", params=params or None)
        return [ImageQuery(**_normalize_image_query_payload(item)) for item in _coerce_image_query_items(payload)]

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

    def ask_async(
        self,
        detector: Union[Detector, str],
        image: Union[str, bytes, IO[bytes]],
        *,
        wait: Optional[Union[bool, float]] = None,
        confidence_threshold: Optional[float] = None,
        metadata: Optional[Union[Mapping[str, Any], str]] = None,
        inspection_id: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> ImageQuery:
        return self.submit_image_query(
            detector=detector,
            image=image,
            wait=wait,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
            prompt=prompt,
        )

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
        payload = _prepare_feedback_payload(feedback, kwargs)
        response = self._http.post_json("/v1/feedback", json=payload)
        return response or {}

    def delete_image_query(self, image_query_id: str) -> None:
        """Delete an image query if the backend supports the operation."""

        self._http.delete(f"/v1/image-queries/{image_query_id}")


class AsyncIntelliOptics:
    """Async variant of :class:`IntelliOptics` built on top of ``httpx``."""

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
        self._http = AsyncHttpClient(
            base_url=endpoint,
            api_token=api_token,
            verify=verify,
            timeout=timeout,
        )
        self.experimental = ExperimentalApi(async_client=self)

    async def close(self) -> None:
        await self._http.close()

    async def __aenter__(self) -> "AsyncIntelliOptics":  # pragma: no cover - trivial context manager
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover
        await self.close()

    async def whoami(self) -> UserIdentity:
        data = await self._http.get_json("/v1/users/me")
        return UserIdentity(**data)

    async def create_detector(
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

        data = await self._http.post_json("/v1/detectors", json=payload)
        return Detector(**data)

    async def list_detectors(self) -> list[Detector]:
        payload = await self._http.get_json("/v1/detectors")
        items = payload.get("items") if isinstance(payload, Mapping) else payload
        if not isinstance(items, list):
            items = []
        return [Detector(**item) for item in items]

    async def get_detector(self, detector_id: str) -> Detector:
        payload = await self._http.get_json(f"/v1/detectors/{detector_id}")
        return Detector(**payload)

    async def submit_image_query(
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
        form, files = _build_image_query_request(
            detector,
            image,
            prompt=prompt,
            wait=wait,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
        )

        payload = await self._http.post_json("/v1/image-queries", data=form, files=files)
        return ImageQuery(**_normalize_image_query_payload(payload))

    async def submit_image_query_json(
        self,
        detector: Optional[Union[Detector, str]] = None,
        *,
        image: Optional[str] = None,
        wait: Optional[bool] = None,
    ) -> ImageQuery:
        detector_id = detector.id if isinstance(detector, Detector) else detector
        payload = {"detector_id": detector_id, "image": image, "wait": wait}
        json_payload = {key: value for key, value in payload.items() if value is not None}
        response = await self._http.post_json("/v1/image-queries-json", json=json_payload)
        return ImageQuery(**_normalize_image_query_payload(response))

    async def get_image_query(self, image_query_id: str) -> ImageQuery:
        payload = await self._http.get_json(f"/v1/image-queries/{image_query_id}")
        return ImageQuery(**_normalize_image_query_payload(payload))

    async def list_image_queries(
        self,
        *,
        detector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[ImageQuery]:
        params = {
            "detector_id": detector_id,
            "status": status,
            "limit": limit,
            "cursor": cursor,
        }
        params = {key: value for key, value in params.items() if value is not None}
        payload = await self._http.get_json("/v1/image-queries", params=params or None)
        return [ImageQuery(**_normalize_image_query_payload(item)) for item in _coerce_image_query_items(payload)]

    async def get_result(self, image_query_id: str) -> QueryResult:
        payload = await self._http.get_json(f"/v1/image-queries/{image_query_id}")
        normalized = _normalize_image_query_payload(payload)
        normalized.pop("detector_id", None)
        return QueryResult(**normalized)

    async def ask_ml(
        self, detector: Union[Detector, str], image: Union[str, bytes, IO[bytes]], wait: Optional[bool] = None
    ) -> ImageQuery:
        return await self.submit_image_query(detector=detector, image=image, wait=wait)

    async def ask_async(
        self,
        detector: Union[Detector, str],
        image: Union[str, bytes, IO[bytes]],
        *,
        wait: Optional[Union[bool, float]] = None,
        confidence_threshold: Optional[float] = None,
        metadata: Optional[Union[Mapping[str, Any], str]] = None,
        inspection_id: Optional[str] = None,
        prompt: Optional[str] = None,
    ) -> ImageQuery:
        return await self.submit_image_query(
            detector=detector,
            image=image,
            wait=wait,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
            prompt=prompt,
        )

    async def ask_confident(
        self,
        detector: Union[Detector, str],
        image: Union[str, bytes, IO[bytes]],
        *,
        confidence_threshold: float = 0.9,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query = await self.submit_image_query(detector=detector, image=image)
        return await self.wait_for_confident_result(
            query,
            confidence_threshold=confidence_threshold,
            timeout_sec=timeout_sec,
            poll_interval=poll_interval,
        )

    async def wait_for_confident_result(
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
            query = await self.get_image_query(query_id)
            if query.status in {"DONE", "ERROR"}:
                if query.confidence is None or query.confidence >= confidence_threshold:
                    return query
            if time.time() >= deadline:
                return query
            await asyncio.sleep(poll_interval)

    async def add_label(
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
        return await self._http.post_json("/v1/labels", json=serialized)

    async def submit_feedback(
        self,
        feedback: Optional[Union[FeedbackIn, Mapping[str, Any]]] = None,
        **kwargs: Any,
    ) -> Dict[str, Any]:
        payload = _prepare_feedback_payload(feedback, kwargs)
        response = await self._http.post_json("/v1/feedback", json=payload)
        return response or {}

    async def delete_image_query(self, image_query_id: str) -> None:
        await self._http.delete(f"/v1/image-queries/{image_query_id}")


class ExperimentalApi:
    """Helper surface for preview and power-user workflows.

    The backing API currently exposes a limited set of experimental endpoints. When
    a method is not implemented by the server this class raises
    :class:`ExperimentalFeatureUnavailable` with a descriptive error instead of an
    ``AttributeError``.
    """

    def __init__(
        self,
        *,
        sync_client: IntelliOptics | None = None,
        async_client: AsyncIntelliOptics | None = None,
    ) -> None:
        if sync_client is None and async_client is None:
            raise ValueError("ExperimentalApi requires either a sync or async client.")
        self._sync_client = sync_client
        self._async_client = async_client

    # ------------------------------------------------------------------
    # Sync helpers
    # ------------------------------------------------------------------
    def _require_sync(self) -> IntelliOptics:
        if self._sync_client is None:
            raise IntelliOpticsClientError(
                "This ExperimentalApi instance is bound to an async client; use the 'a*' coroutine helpers instead."
            )
        return self._sync_client

    def list_image_queries(
        self,
        *,
        detector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[ImageQuery]:
        client = self._require_sync()
        return client.list_image_queries(
            detector_id=detector_id,
            status=status,
            limit=limit,
            cursor=cursor,
        )

    def delete_image_query(self, image_query_id: str) -> None:
        client = self._require_sync()
        client.delete_image_query(image_query_id)

    # ------------------------------------------------------------------
    # Async helpers
    # ------------------------------------------------------------------
    def _require_async(self) -> AsyncIntelliOptics:
        if self._async_client is None:
            raise IntelliOpticsClientError(
                "This ExperimentalApi instance is bound to a sync client; use the synchronous helpers."
            )
        return self._async_client

    async def alist_image_queries(
        self,
        *,
        detector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[ImageQuery]:
        client = self._require_async()
        return await client.list_image_queries(
            detector_id=detector_id,
            status=status,
            limit=limit,
            cursor=cursor,
        )

    async def adelete_image_query(self, image_query_id: str) -> None:
        client = self._require_async()
        await client.delete_image_query(image_query_id)

    # ------------------------------------------------------------------
    # Graceful fallback for not-yet-implemented helpers
    # ------------------------------------------------------------------
    def __getattr__(self, item: str):  # pragma: no cover - dynamic dispatch
        if item.startswith("a"):

            async def _async_placeholder(*_: Any, **__: Any) -> Any:
                raise ExperimentalFeatureUnavailable(item)

            return _async_placeholder

        def _sync_placeholder(*_: Any, **__: Any) -> Any:
            raise ExperimentalFeatureUnavailable(item)

        return _sync_placeholder
