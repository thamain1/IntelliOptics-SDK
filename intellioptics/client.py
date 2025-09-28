"""High level Python SDK for the IntelliOptics HTTP API."""

from __future__ import annotations

from __future__ import annotations

import asyncio
import json
import os
import time
import zipfile
from collections.abc import Mapping, Sequence
from io import BytesIO
from pathlib import Path
from typing import Any, Dict, IO, Iterable, Optional, Union

from ._http import AsyncHttpClient, HttpClient
from ._img import to_jpeg_bytes
from .errors import ApiTokenError, ExperimentalFeatureUnavailable, IntelliOpticsClientError
from .models import (
    Action,
    Condition,
    Detector,
    FeedbackIn,
    HTTPResponse,
    ImageQuery,
    PaginatedRuleList,
    PayloadTemplate,
    QueryResult,
    Rule,
    UserIdentity,
    WebhookAction,
)


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


def _serialize_model(model: Any) -> Dict[str, Any]:
    serializer = getattr(model, "model_dump", None) or getattr(model, "dict", None)
    if serializer is not None:
        return serializer(exclude_none=True)
    if isinstance(model, Mapping):
        return dict(model)
    raise TypeError(f"Unsupported model type: {type(model)!r}")


def _normalize_action_list(actions: Any) -> Optional[list[Action]]:
    if actions is None:
        return None
    if isinstance(actions, Action):
        return [actions]
    if isinstance(actions, Mapping):
        return [Action(**dict(actions))]
    if isinstance(actions, Sequence) and not isinstance(actions, (str, bytes)):
        normalized: list[Action] = []
        for item in actions:
            if isinstance(item, Action):
                normalized.append(item)
            elif isinstance(item, Mapping):
                normalized.append(Action(**dict(item)))
            else:
                raise TypeError("Actions must be Action models or mapping objects")
        return normalized
    raise TypeError("Actions must be Action models or mapping objects")


def _normalize_webhook_list(webhook_actions: Any) -> Optional[list[WebhookAction]]:
    if webhook_actions is None:
        return None
    if isinstance(webhook_actions, WebhookAction):
        return [webhook_actions]
    if isinstance(webhook_actions, Mapping):
        return [WebhookAction(**dict(webhook_actions))]
    if isinstance(webhook_actions, Sequence) and not isinstance(webhook_actions, (str, bytes)):
        normalized: list[WebhookAction] = []
        for item in webhook_actions:
            if isinstance(item, WebhookAction):
                normalized.append(item)
            elif isinstance(item, Mapping):
                normalized.append(WebhookAction(**dict(item)))
            else:
                raise TypeError("Webhook actions must be WebhookAction models or mapping objects")
        return normalized
    raise TypeError("Webhook actions must be WebhookAction models or mapping objects")


def _ensure_condition(condition: Condition | Mapping[str, Any]) -> Condition:
    if isinstance(condition, Condition):
        return condition
    return Condition(**dict(condition))


def _ensure_payload_template(template: PayloadTemplate | Mapping[str, Any] | None) -> Optional[PayloadTemplate]:
    if template is None or isinstance(template, PayloadTemplate):
        return template
    return PayloadTemplate(**dict(template))


def _detector_identifier(detector: Union[Detector, str]) -> str:
    detector_id = detector.id if isinstance(detector, Detector) else detector
    if not detector_id:
        raise ValueError("Detector identifier must be provided")
    return detector_id


def _dump_metadata(metadata: Optional[Union[Mapping[str, Any], str]]) -> Optional[Union[str, Mapping[str, Any]]]:
    if metadata is None:
        return None
    if isinstance(metadata, Mapping):
        return json.dumps(dict(metadata))
    return metadata


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

    Provides a richer set of helpers for experimental endpoints. When the
    backing service omits a feature the helpers raise
    :class:`ExperimentalFeatureUnavailable` rather than exposing partially
    initialised state.
    """

    def __init__(
        self,
        endpoint: str | None = None,
        api_token: str | None = None,
        *,
        disable_tls_verification: bool | None = None,
        timeout: float = 30.0,
        sync_client: IntelliOptics | None = None,
        async_client: AsyncIntelliOptics | None = None,
    ) -> None:
        self._sync_client = sync_client
        self._async_client = async_client
        self._http: HttpClient | None = None
        self._async_http: AsyncHttpClient | None = None
        self._owns_sync_http = False

        if sync_client is None and async_client is None:
            endpoint = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT")
            api_token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN")
            if not api_token:
                raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")
            if not endpoint:
                raise IntelliOpticsClientError("Missing INTELLIOPTICS_ENDPOINT")

            verify = not (disable_tls_verification or os.getenv("DISABLE_TLS_VERIFY") == "1")
            self._http = HttpClient(
                base_url=endpoint,
                api_token=api_token,
                verify=verify,
                timeout=timeout,
            )
            self._owns_sync_http = True

        if async_client is not None:
            self._async_http = async_client._http

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._owns_sync_http and self._http is not None:
            self._http.close()

    def _sync_http(self) -> HttpClient:
        if self._sync_client is not None:
            return self._sync_client._http
        if self._http is not None:
            return self._http
        raise IntelliOpticsClientError(
            "This ExperimentalApi instance is bound to an async client; use the 'a*' coroutine helpers instead."
        )

    def _async_http_client(self) -> AsyncHttpClient:
        if self._async_client is not None:
            return self._async_client._http
        if self._async_http is not None:
            return self._async_http
        raise IntelliOpticsClientError(
            "This ExperimentalApi instance is bound to a sync client; use the synchronous helpers."
        )

    def _sync_client_required(self) -> IntelliOptics:
        if self._sync_client is None:
            raise IntelliOpticsClientError(
                "This ExperimentalApi instance is bound to an async client; use the 'a*' coroutine helpers instead."
            )
        return self._sync_client

    def _ensure_actions_payload(self, actions: Any) -> Optional[list[Dict[str, Any]]]:
        normalized = _normalize_action_list(actions)
        if not normalized:
            return None
        return [_serialize_model(action) for action in normalized]

    def _ensure_webhook_payload(self, webhook_actions: Any) -> Optional[list[Dict[str, Any]]]:
        normalized = _normalize_webhook_list(webhook_actions)
        if not normalized:
            return None
        return [_serialize_model(action) for action in normalized]

    def _build_alert_payload(
        self,
        detector: Union[Detector, str],
        name: str,
        condition: Condition | Mapping[str, Any],
        *,
        actions: Any = None,
        webhook_actions: Any = None,
        enabled: bool = True,
        snooze_time_enabled: bool = False,
        snooze_time_value: int = 3600,
        snooze_time_unit: str = "SECONDS",
        human_review_required: bool = False,
    ) -> tuple[str, Dict[str, Any]]:
        detector_id = _detector_identifier(detector)
        condition_model = _ensure_condition(condition)

        actions_payload = self._ensure_actions_payload(actions)
        webhook_payload = self._ensure_webhook_payload(webhook_actions)

        if not actions_payload and not webhook_payload:
            raise ValueError("Provide at least one action or webhook action for the alert")

        payload: Dict[str, Any] = {
            "name": name,
            "condition": _serialize_model(condition_model),
            "enabled": enabled,
            "snooze_time_enabled": snooze_time_enabled,
            "snooze_time_value": snooze_time_value,
            "snooze_time_unit": snooze_time_unit.upper(),
            "human_review_required": human_review_required,
        }

        if actions_payload is not None:
            payload["actions"] = actions_payload
        if webhook_payload is not None:
            payload["webhook_actions"] = webhook_payload

        return detector_id, payload

    # ------------------------------------------------------------------
    # Detector helpers
    # ------------------------------------------------------------------
    def create_bounding_box_detector(
        self,
        name: str,
        query: str,
        class_name: str,
        *,
        max_num_bboxes: int | None = None,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Optional[Union[Mapping[str, Any], str]] = None,
    ) -> Detector:
        payload: Dict[str, Any] = {
            "name": name,
            "query": query,
            "class_name": class_name,
            "max_num_bboxes": max_num_bboxes,
            "group_name": group_name,
            "confidence_threshold": confidence_threshold,
            "patience_time": patience_time,
            "pipeline_config": pipeline_config,
        }

        serialized_metadata = _dump_metadata(metadata)
        if serialized_metadata is not None:
            payload["metadata"] = serialized_metadata

        payload = {key: value for key, value in payload.items() if value is not None}
        data = self._sync_http().post_json("/v1/detectors/bounding-box", json=payload)
        return Detector(**data)

    def create_text_recognition_detector(
        self,
        name: str,
        query: str,
        *,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Optional[Union[Mapping[str, Any], str]] = None,
    ) -> Detector:
        payload: Dict[str, Any] = {
            "name": name,
            "query": query,
            "group_name": group_name,
            "confidence_threshold": confidence_threshold,
            "patience_time": patience_time,
            "pipeline_config": pipeline_config,
        }

        serialized_metadata = _dump_metadata(metadata)
        if serialized_metadata is not None:
            payload["metadata"] = serialized_metadata

        payload = {key: value for key, value in payload.items() if value is not None}
        data = self._sync_http().post_json("/v1/detectors/text-recognition", json=payload)
        return Detector(**data)

    def update_detector_name(self, detector: Union[Detector, str], name: str) -> None:
        detector_id = _detector_identifier(detector)
        self._sync_http().patch_json(f"/v1/detectors/{detector_id}", json={"name": name})

    def reset_detector(self, detector: Union[Detector, str]) -> None:
        detector_id = _detector_identifier(detector)
        self._sync_http().post_json(f"/v1/detectors/{detector_id}/reset")

    def download_mlbinary(self, detector: Union[Detector, str], output_dir: str) -> None:
        detector_id = _detector_identifier(detector)
        response = self._sync_http().request_raw("GET", f"/v1/detectors/{detector_id}/mlbinary")
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        content = response.content or b""
        if not content:
            return

        ctype = response.headers.get("Content-Type", "").lower()
        if "zip" in ctype or content.startswith(b"PK"):
            with zipfile.ZipFile(BytesIO(content)) as archive:
                archive.extractall(output_path)
            return

        disposition = response.headers.get("Content-Disposition", "")
        filename = None
        if "filename=" in disposition:
            filename = disposition.split("filename=")[-1].strip().strip('"')
        if not filename:
            filename = f"{detector_id}.bin"

        file_path = output_path / filename
        with open(file_path, "wb") as handle:
            handle.write(content)

    def get_detector_metrics(self, detector: Union[Detector, str]) -> Dict[str, Any]:
        detector_id = _detector_identifier(detector)
        payload = self._sync_http().get_json(f"/v1/detectors/{detector_id}/metrics")
        return dict(payload) if isinstance(payload, Mapping) else {"metrics": payload}

    def get_detector_evaluation(self, detector: Union[Detector, str]) -> Dict[str, Any]:
        detector_id = _detector_identifier(detector)
        payload = self._sync_http().get_json(f"/v1/detectors/{detector_id}/evaluation")
        return dict(payload) if isinstance(payload, Mapping) else {"evaluation": payload}

    def create_note(
        self,
        detector: Union[Detector, str],
        note: str,
        image: Optional[Union[str, bytes, IO[bytes]]] = None,
    ) -> None:
        detector_id = _detector_identifier(detector)
        files = None
        if image is not None:
            image_bytes = to_jpeg_bytes(image)
            files = {"image": ("note.jpg", image_bytes, "image/jpeg")}

        data = {"note": note}
        self._sync_http().post_json(f"/v1/detectors/{detector_id}/notes", data=data, files=files)

    def get_notes(self, detector: Union[Detector, str]) -> Dict[str, Any]:
        detector_id = _detector_identifier(detector)
        payload = self._sync_http().get_json(f"/v1/detectors/{detector_id}/notes")
        return dict(payload) if isinstance(payload, Mapping) else {"notes": payload}

    # ------------------------------------------------------------------
    # Alert & rule helpers
    # ------------------------------------------------------------------
    def create_alert(
        self,
        detector: Union[Detector, str],
        name: str,
        condition: Condition | Mapping[str, Any],
        actions: Any | None = None,
        webhook_actions: Any | None = None,
        *,
        enabled: bool = True,
        snooze_time_enabled: bool = False,
        snooze_time_value: int = 3600,
        snooze_time_unit: str = "SECONDS",
        human_review_required: bool = False,
    ) -> Rule:
        detector_id, payload = self._build_alert_payload(
            detector,
            name,
            condition,
            actions=actions,
            webhook_actions=webhook_actions,
            enabled=enabled,
            snooze_time_enabled=snooze_time_enabled,
            snooze_time_value=snooze_time_value,
            snooze_time_unit=snooze_time_unit,
            human_review_required=human_review_required,
        )

        data = self._sync_http().post_json(f"/v1/detectors/{detector_id}/alerts", json=payload)
        return Rule(**data)

    def create_rule(
        self,
        detector: Union[Detector, str],
        rule_name: str,
        channel: str,
        recipient: str,
        *,
        alert_on: str = "CHANGED_TO",
        enabled: bool = True,
        include_image: bool = False,
        condition_parameters: Optional[Union[str, Mapping[str, Any]]] = None,
        snooze_time_enabled: bool = False,
        snooze_time_value: int = 3600,
        snooze_time_unit: str = "SECONDS",
        human_review_required: bool = False,
    ) -> Rule:
        if condition_parameters is None:
            parameters: Mapping[str, Any] = {}
        elif isinstance(condition_parameters, str):
            parameters = json.loads(condition_parameters)
        elif isinstance(condition_parameters, Mapping):
            parameters = condition_parameters
        else:
            raise TypeError("condition_parameters must be a mapping or JSON string")

        condition = Condition(verb=alert_on, parameters=dict(parameters))
        action = self.make_action(channel, recipient, include_image)
        return self.create_alert(
            detector,
            rule_name,
            condition,
            actions=[action],
            enabled=enabled,
            snooze_time_enabled=snooze_time_enabled,
            snooze_time_value=snooze_time_value,
            snooze_time_unit=snooze_time_unit,
            human_review_required=human_review_required,
        )

    def list_rules(self, page: int = 1, page_size: int = 10) -> PaginatedRuleList:
        params = {"page": page, "page_size": page_size}
        payload = self._sync_http().get_json("/v1/rules", params=params)
        return PaginatedRuleList(**payload)

    def get_rule(self, action_id: int) -> Rule:
        payload = self._sync_http().get_json(f"/v1/rules/{action_id}")
        return Rule(**payload)

    def delete_rule(self, action_id: int) -> None:
        self._sync_http().delete(f"/v1/rules/{action_id}")

    def delete_all_rules(self, detector: Union[Detector, str] | None = None) -> int:
        params = None
        if detector is not None:
            params = {"detector_id": _detector_identifier(detector)}
        payload = self._sync_http().delete("/v1/rules", params=params)
        if isinstance(payload, Mapping):
            for key in ("deleted", "count", "removed"):
                value = payload.get(key)
                if isinstance(value, int):
                    return value
        if isinstance(payload, int):
            return payload
        return 0

    def make_action(self, channel: str, recipient: str, include_image: bool) -> Action:
        return Action(channel=channel.upper(), recipient=recipient, include_image=bool(include_image))

    def make_condition(self, verb: str, parameters: Mapping[str, Any]) -> Condition:
        return Condition(verb=verb, parameters=dict(parameters))

    def make_payload_template(self, template: str, headers: Optional[Dict[str, str]] = None) -> PayloadTemplate:
        return PayloadTemplate(template=template, headers=headers)

    def make_webhook_action(
        self,
        url: str,
        include_image: bool,
        payload_template: PayloadTemplate | Mapping[str, Any] | None = None,
    ) -> WebhookAction:
        template = _ensure_payload_template(payload_template)
        return WebhookAction(url=url, include_image=include_image, payload_template=template)

    def get_raw_headers(self) -> Dict[str, str]:
        http = self._sync_http()
        return dict(http.headers)

    def make_generic_api_request(
        self,
        *,
        endpoint: str,
        method: str,
        headers: Optional[Dict[str, str]] = None,
        body: Optional[Dict[str, Any]] = None,
        files: Any = None,
    ) -> HTTPResponse:
        if not endpoint.startswith("/"):
            raise ValueError("endpoint must start with '/' and be relative to the API base")

        request_kwargs: Dict[str, Any] = {}
        if files is not None:
            request_kwargs["files"] = files
            if body is not None:
                request_kwargs["data"] = body
        elif body is not None:
            request_kwargs["json"] = body

        response = self._sync_http().request_raw(method.upper(), endpoint, headers=headers, **request_kwargs)
        content_type = response.headers.get("Content-Type", "").lower()
        if "json" in content_type:
            parsed_body: Any = response.json()
        elif "text" in content_type or "xml" in content_type or "html" in content_type:
            parsed_body = response.text
        else:
            parsed_body = response.content

        return HTTPResponse(status_code=response.status_code, headers=dict(response.headers), body=parsed_body)

    # ------------------------------------------------------------------
    # Bridged helpers to the core client
    # ------------------------------------------------------------------
    def list_image_queries(
        self,
        *,
        detector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[ImageQuery]:
        client = self._sync_client_required()
        return client.list_image_queries(
            detector_id=detector_id,
            status=status,
            limit=limit,
            cursor=cursor,
        )

    def delete_image_query(self, image_query_id: str) -> None:
        client = self._sync_client_required()
        client.delete_image_query(image_query_id)

    async def alist_image_queries(
        self,
        *,
        detector_id: Optional[str] = None,
        status: Optional[str] = None,
        limit: Optional[int] = None,
        cursor: Optional[str] = None,
    ) -> list[ImageQuery]:
        http = self._async_http_client()
        params = {"detector_id": detector_id, "status": status, "limit": limit, "cursor": cursor}
        params = {key: value for key, value in params.items() if value is not None}
        payload = await http.get_json("/v1/image-queries", params=params or None)
        return [ImageQuery(**_normalize_image_query_payload(item)) for item in _coerce_image_query_items(payload)]

    async def adelete_image_query(self, image_query_id: str) -> None:
        http = self._async_http_client()
        await http.delete(f"/v1/image-queries/{image_query_id}")

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
