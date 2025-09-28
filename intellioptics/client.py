"""High level Python SDK for the IntelliOptics HTTP API."""

from __future__ import annotations

import asyncio
import json
import os
import time
from os import PathLike
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence, Union

from ._http import AsyncHttpClient, HttpClient
from ._img import to_jpeg_bytes
from .errors import ApiTokenError, ExperimentalFeatureUnavailable
from .models import (
    Action,
    Condition,
    Detector,
    FeedbackIn,
    HTTPResponse,
    ImageQuery,
    PayloadTemplate,
    QueryResult,
    Rule,
    UserIdentity,
    WebhookAction,
)


ImageArg = Union[str, bytes, PathLike[str], Any]


def _detector_identifier(detector: Detector | str | None) -> str | None:
    if detector is None:
        return None
    if isinstance(detector, Detector):
        return detector.id
    if isinstance(detector, str):
        return detector
    raise TypeError("detector must be a Detector or string identifier")


def _serialize_model(model: Any) -> dict[str, Any]:
    if hasattr(model, "model_dump"):
        data = model.model_dump()  # type: ignore[call-arg]
    elif hasattr(model, "dict"):
        data = model.dict()  # type: ignore[call-arg]
    elif isinstance(model, Mapping):
        data = dict(model)
    else:
        raise TypeError(f"Cannot serialise object of type {type(model)!r}")
    return {k: v for k, v in data.items() if v is not None}


def _dump_metadata(metadata: Mapping[str, Any] | str | None) -> str | None:
    if metadata is None:
        return None
    if isinstance(metadata, str):
        return metadata
    if isinstance(metadata, Mapping):
        return json.dumps(metadata)
    raise TypeError("metadata must be a mapping or string")


def _serialize_wait(wait: bool | float | None) -> str | float | None:
    if wait is None:
        return None
    if isinstance(wait, bool):
        return "true" if wait else "false"
    return wait


def _build_image_query_request(
    detector: Detector | str | None,
    image: ImageArg | None,
    *,
    prompt: str | None,
    wait: bool | float | None,
    confidence_threshold: float | None,
    metadata: Mapping[str, Any] | str | None,
    inspection_id: str | None,
) -> tuple[dict[str, Any], dict[str, tuple[str, bytes, str]] | None]:
    detector_id = _detector_identifier(detector)
    form: dict[str, Any] = {
        "detector_id": detector_id,
        "prompt": prompt,
        "wait": _serialize_wait(wait),
        "confidence_threshold": confidence_threshold,
        "metadata": _dump_metadata(metadata),
        "inspection_id": inspection_id,
    }

    files: dict[str, tuple[str, bytes, str]] | None = None
    if image is not None:
        payload = to_jpeg_bytes(image)
        files = {"image": ("image.jpg", payload, "image/jpeg")}

    form = {key: value for key, value in form.items() if value is not None}
    return form, files


def _resolve_status(payload: Mapping[str, Any]) -> str:
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


def _normalize_image_query_payload(payload: Mapping[str, Any]) -> dict[str, Any]:
    result_block = payload.get("result")
    if not isinstance(result_block, Mapping):
        result_block = {}

    data: dict[str, Any] = {
        "id": payload.get("id") or payload.get("image_query_id"),
        "detector_id": payload.get("detector_id"),
        "status": _resolve_status(payload),
        "result_type": payload.get("result_type"),
    }

    confidence = payload.get("confidence", result_block.get("confidence"))
    if confidence is not None:
        data["confidence"] = confidence

    label = payload.get("label") or result_block.get("label") or payload.get("answer")
    if label is not None:
        data["label"] = label

    extra: dict[str, Any] = {}
    raw_extra = payload.get("extra")
    if isinstance(raw_extra, Mapping):
        extra.update(raw_extra)

    for key in ("latency_ms", "model_version", "done_processing"):
        value = payload.get(key)
        if value is not None:
            extra.setdefault(key, value)

    for key, value in result_block.items():
        if key not in {"label", "confidence"} and value is not None:
            extra.setdefault(key, value)

    if extra:
        data["extra"] = extra

    return data


def _coerce_image_query_items(payload: Any) -> list[Mapping[str, Any]]:
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


def _prepare_feedback_payload(
    feedback: FeedbackIn | Mapping[str, Any] | None,
    kwargs: Mapping[str, Any],
) -> dict[str, Any]:
    if feedback is not None and kwargs:
        raise ValueError("Provide feedback as a model/dict or as keyword arguments, not both.")

    if feedback is None:
        payload = dict(kwargs)
    elif isinstance(feedback, FeedbackIn):
        payload = _serialize_model(feedback)
    elif isinstance(feedback, Mapping):
        payload = dict(feedback)
    else:
        raise TypeError("feedback must be FeedbackIn or mapping")

    return {k: v for k, v in payload.items() if v is not None}


def _parse_jsonish(data: Mapping[str, Any] | str | None) -> Mapping[str, Any]:
    if data is None:
        return {}
    if isinstance(data, Mapping):
        return dict(data)
    if isinstance(data, str):
        if not data.strip():
            return {}
        try:
            loaded = json.loads(data)
        except json.JSONDecodeError as exc:  # pragma: no cover - defensive
            raise ValueError("Expected valid JSON string") from exc
        if not isinstance(loaded, Mapping):
            raise ValueError("JSON string must decode to an object")
        return dict(loaded)
    raise TypeError("Expected mapping or JSON string")


def _ensure_condition(condition: Condition | Mapping[str, Any]) -> Condition:
    if isinstance(condition, Condition):
        return condition
    if isinstance(condition, Mapping):
        return Condition(**condition)
    raise TypeError("condition must be a Condition or mapping")


def _ensure_actions_payload(actions: Any) -> list[dict[str, Any]] | None:
    if actions is None:
        return None
    if isinstance(actions, (Action, Mapping)):
        return [_serialize_model(actions)]
    if isinstance(actions, Iterable):
        serialized: list[dict[str, Any]] = []
        for item in actions:
            serialized.append(_serialize_model(item))
        return serialized
    raise TypeError("actions must be an Action, mapping, or iterable of those")


def _ensure_webhook_payload(webhook_actions: Any) -> list[dict[str, Any]] | None:
    if webhook_actions is None:
        return None
    if isinstance(webhook_actions, (WebhookAction, Mapping)):
        return [_serialize_model(webhook_actions)]
    if isinstance(webhook_actions, Iterable):
        return [_serialize_model(item) for item in webhook_actions]
    raise TypeError("webhook_actions must be WebhookAction, mapping, or iterable")


def _build_alert_payload(
    detector: Detector | str,
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
) -> tuple[str, dict[str, Any]]:
    detector_id = _detector_identifier(detector)
    if detector_id is None:
        raise ValueError("detector is required")

    condition_model = _ensure_condition(condition)
    actions_payload = _ensure_actions_payload(actions)
    webhook_payload = _ensure_webhook_payload(webhook_actions)

    if not actions_payload and not webhook_payload:
        raise ValueError("Provide at least one action or webhook action for the alert")

    payload: dict[str, Any] = {
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


def _extract_filename(headers: Mapping[str, str]) -> str:
    disposition = headers.get("Content-Disposition") or headers.get("content-disposition")
    if not disposition:
        return "model.bin"
    for part in disposition.split(";"):
        part = part.strip()
        if part.startswith("filename="):
            filename = part.split("=", 1)[1].strip().strip('"')
            if filename:
                return filename
    return "model.bin"


def _maybe_parse_json(response: Any) -> Any:
    headers = getattr(response, "headers", {}) or {}
    content_type = (headers.get("Content-Type") or headers.get("content-type") or "").lower()
    if "json" in content_type:
        try:
            return response.json()
        except Exception:  # pragma: no cover - if body is empty
            return {}
    return response.text


class IntelliOptics:
    """Synchronous IntelliOptics API client."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_token: str | None = None,
        *,
        disable_tls_verification: bool | None = None,
        timeout: float = 30.0,
    ) -> None:
        token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN") or os.getenv("INTELLIOOPTICS_API_TOKEN")
        if not token:
            raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")

        base_url = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT") or "https://intellioptics-api-37558.azurewebsites.net"
        disable_env = os.getenv("DISABLE_TLS_VERIFY") == "1"
        verify = not (disable_tls_verification or disable_env)

        self._http = HttpClient(base_url=base_url, api_token=token, verify=verify, timeout=timeout)
        self.experimental = ExperimentalApi(sync_client=self)

    # ------------------------------------------------------------------
    # Lifecycle helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        self._http.close()

    def __enter__(self) -> "IntelliOptics":  # pragma: no cover - convenience
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - convenience
        self.close()

    # ------------------------------------------------------------------
    # Core endpoints
    # ------------------------------------------------------------------
    def whoami(self) -> UserIdentity:
        payload = self._http.get_json("/v1/users/me")
        return UserIdentity(**payload)

    def create_detector(self, name: str, *, mode: str, query_text: str, threshold: float | None = None) -> Detector:
        payload: dict[str, Any] = {
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
        if not isinstance(items, Sequence):
            items = []
        return [Detector(**item) for item in items]

    def get_detector(self, detector_id: str) -> Detector:
        payload = self._http.get_json(f"/v1/detectors/{detector_id}")
        return Detector(**payload)

    def submit_image_query(
        self,
        detector: Detector | str | None = None,
        image: ImageArg | None = None,
        *,
        prompt: str | None = None,
        wait: bool | float | None = None,
        confidence_threshold: float | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
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
        detector: Detector | str | None = None,
        *,
        image: str | None = None,
        wait: bool | float | None = None,
        confidence_threshold: float | None = None,
        metadata: Mapping[str, Any] | None = None,
        inspection_id: str | None = None,
        prompt: str | None = None,
    ) -> ImageQuery:
        detector_id = _detector_identifier(detector)
        payload: dict[str, Any] = {
            "detector_id": detector_id,
            "image": image,
            "wait": wait,
            "confidence_threshold": confidence_threshold,
            "metadata": dict(metadata) if isinstance(metadata, Mapping) else metadata,
            "inspection_id": inspection_id,
            "prompt": prompt,
        }
        serialized = {key: value for key, value in payload.items() if value is not None}
        response = self._http.post_json("/v1/image-queries-json", json=serialized)
        return ImageQuery(**_normalize_image_query_payload(response))

    def get_image_query(self, image_query_id: str) -> ImageQuery:
        payload = self._http.get_json(f"/v1/image-queries/{image_query_id}")
        return ImageQuery(**_normalize_image_query_payload(payload))

    def list_image_queries(
        self,
        *,
        detector_id: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
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

    def submit_feedback(
        self,
        feedback: FeedbackIn | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = _prepare_feedback_payload(feedback, kwargs)
        response = self._http.post_json("/v1/feedback", json=payload)
        return response or {}

    def add_label(
        self,
        image_query_id: str,
        label: str,
        *,
        confidence: float | None = None,
        detector_id: str | None = None,
        user_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "image_query_id": image_query_id,
            "label": label,
            "confidence": confidence,
            "detector_id": detector_id,
            "user_id": user_id,
            "metadata": dict(metadata) if isinstance(metadata, Mapping) else metadata,
        }
        serialized = {key: value for key, value in payload.items() if value is not None}
        return self._http.post_json("/v1/labels", json=serialized)

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def ask_ml(self, detector: Detector | str, image: ImageArg, wait: bool | None = None) -> ImageQuery:
        return self.submit_image_query(detector=detector, image=image, wait=wait)

    def ask_async(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        wait: bool | float | None = None,
        confidence_threshold: float | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
        prompt: str | None = None,
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
        detector: Detector | str,
        image: ImageArg,
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
        image_query: ImageQuery | str,
        *,
        confidence_threshold: float = 0.9,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        deadline = time.time() + timeout_sec
        last_query: ImageQuery | None = None

        while True:
            current = self.get_image_query(query_id)
            last_query = current
            if current.status in {"DONE", "ERROR"}:
                if current.confidence is None or current.confidence >= confidence_threshold:
                    return current
            if time.time() >= deadline:
                return last_query
            time.sleep(poll_interval)


class AsyncIntelliOptics:
    """Async variant of :class:`IntelliOptics`."""

    def __init__(
        self,
        endpoint: str | None = None,
        api_token: str | None = None,
        *,
        disable_tls_verification: bool | None = None,
        timeout: float = 30.0,
    ) -> None:
        token = api_token or os.getenv("INTELLIOPTICS_API_TOKEN") or os.getenv("INTELLIOOPTICS_API_TOKEN")
        if not token:
            raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")

        base_url = endpoint or os.getenv("INTELLIOPTICS_ENDPOINT") or "https://intellioptics-api-37558.azurewebsites.net"
        disable_env = os.getenv("DISABLE_TLS_VERIFY") == "1"
        verify = not (disable_tls_verification or disable_env)

        self._http = AsyncHttpClient(base_url=base_url, api_token=token, verify=verify, timeout=timeout)
        self.experimental = ExperimentalApi(async_client=self)

    async def close(self) -> None:
        await self._http.close()

    async def __aenter__(self) -> "AsyncIntelliOptics":  # pragma: no cover - convenience
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - convenience
        await self.close()

    async def whoami(self) -> UserIdentity:
        payload = await self._http.get_json("/v1/users/me")
        return UserIdentity(**payload)

    async def create_detector(
        self,
        name: str,
        *,
        mode: str,
        query_text: str,
        threshold: float | None = None,
    ) -> Detector:
        payload: dict[str, Any] = {
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
        if not isinstance(items, Sequence):
            items = []
        return [Detector(**item) for item in items]

    async def get_detector(self, detector_id: str) -> Detector:
        payload = await self._http.get_json(f"/v1/detectors/{detector_id}")
        return Detector(**payload)

    async def submit_image_query(
        self,
        detector: Detector | str | None = None,
        image: ImageArg | None = None,
        *,
        prompt: str | None = None,
        wait: bool | float | None = None,
        confidence_threshold: float | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
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
        detector: Detector | str | None = None,
        *,
        image: str | None = None,
        wait: bool | float | None = None,
        confidence_threshold: float | None = None,
        metadata: Mapping[str, Any] | None = None,
        inspection_id: str | None = None,
        prompt: str | None = None,
    ) -> ImageQuery:
        detector_id = _detector_identifier(detector)
        payload: dict[str, Any] = {
            "detector_id": detector_id,
            "image": image,
            "wait": wait,
            "confidence_threshold": confidence_threshold,
            "metadata": dict(metadata) if isinstance(metadata, Mapping) else metadata,
            "inspection_id": inspection_id,
            "prompt": prompt,
        }
        serialized = {key: value for key, value in payload.items() if value is not None}
        response = await self._http.post_json("/v1/image-queries-json", json=serialized)
        return ImageQuery(**_normalize_image_query_payload(response))

    async def get_image_query(self, image_query_id: str) -> ImageQuery:
        payload = await self._http.get_json(f"/v1/image-queries/{image_query_id}")
        return ImageQuery(**_normalize_image_query_payload(payload))

    async def list_image_queries(
        self,
        *,
        detector_id: str | None = None,
        status: str | None = None,
        limit: int | None = None,
        cursor: str | None = None,
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

    async def submit_feedback(
        self,
        feedback: FeedbackIn | Mapping[str, Any] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        payload = _prepare_feedback_payload(feedback, kwargs)
        response = await self._http.post_json("/v1/feedback", json=payload)
        return response or {}

    async def add_label(
        self,
        image_query_id: str,
        label: str,
        *,
        confidence: float | None = None,
        detector_id: str | None = None,
        user_id: str | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "image_query_id": image_query_id,
            "label": label,
            "confidence": confidence,
            "detector_id": detector_id,
            "user_id": user_id,
            "metadata": dict(metadata) if isinstance(metadata, Mapping) else metadata,
        }
        serialized = {key: value for key, value in payload.items() if value is not None}
        return await self._http.post_json("/v1/labels", json=serialized)

    async def delete_image_query(self, image_query_id: str) -> None:
        await self._http.delete(f"/v1/image-queries/{image_query_id}")

    async def ask_ml(self, detector: Detector | str, image: ImageArg, wait: bool | None = None) -> ImageQuery:
        return await self.submit_image_query(detector=detector, image=image, wait=wait)

    async def ask_async(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        wait: bool | float | None = None,
        confidence_threshold: float | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
        prompt: str | None = None,
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
        detector: Detector | str,
        image: ImageArg,
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
        image_query: ImageQuery | str,
        *,
        confidence_threshold: float = 0.9,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        deadline = time.time() + timeout_sec
        last_query: ImageQuery | None = None

        while True:
            current = await self.get_image_query(query_id)
            last_query = current
            if current.status in {"DONE", "ERROR"}:
                if current.confidence is None or current.confidence >= confidence_threshold:
                    return current
            if time.time() >= deadline:
                return last_query
            await asyncio.sleep(poll_interval)


class ExperimentalApi:
    """Helper for experimental endpoints and workflows."""

    def __init__(
        self,
        *,
        endpoint: str | None = None,
        api_token: str | None = None,
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
        self._config = {
            "endpoint": endpoint,
            "api_token": api_token,
            "disable_tls_verification": disable_tls_verification,
            "timeout": timeout,
        }

        if async_client is not None:
            self._async_http = async_client._http  # type: ignore[attr-defined]

    def __getattr__(self, name: str) -> Any:
        raise ExperimentalFeatureUnavailable(name)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _sync_http(self) -> HttpClient:
        if self._sync_client is not None:
            return self._sync_client._http  # type: ignore[attr-defined]

        if self._http is not None:
            return self._http

        token = self._config.get("api_token") or os.getenv("INTELLIOPTICS_API_TOKEN") or os.getenv(
            "INTELLIOOPTICS_API_TOKEN"
        )
        if not token:
            raise ApiTokenError("Missing INTELLIOPTICS_API_TOKEN")

        base_url = self._config.get("endpoint") or os.getenv("INTELLIOPTICS_ENDPOINT") or "https://intellioptics-api-37558.azurewebsites.net"
        disable_flag = self._config.get("disable_tls_verification")
        disable_env = os.getenv("DISABLE_TLS_VERIFY") == "1"
        verify = not (disable_flag or disable_env)
        timeout = float(self._config.get("timeout", 30.0))

        self._http = HttpClient(base_url=base_url, api_token=token, verify=verify, timeout=timeout)
        self._owns_sync_http = True
        return self._http

    # ------------------------------------------------------------------
    # Public helpers
    # ------------------------------------------------------------------
    def close(self) -> None:
        if self._owns_sync_http and self._http is not None:
            self._http.close()

    def create_alert(
        self,
        detector: Detector | str,
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
    ) -> Rule:
        detector_id, payload = _build_alert_payload(
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
        response = self._sync_http().post_json(f"/v1/detectors/{detector_id}/alerts", json=payload)
        return Rule(**response)

    def create_rule(
        self,
        detector: Detector | str,
        name: str,
        channel: str,
        recipient: str,
        *,
        include_image: bool = False,
        condition_verb: str = "CHANGED_TO",
        condition_parameters: Mapping[str, Any] | str | None = None,
        webhook_url: str | None = None,
        webhook_include_image: bool | None = None,
        webhook_headers: Mapping[str, str] | None = None,
        webhook_payload_template: str | None = None,
    ) -> Rule:
        parameters = _parse_jsonish(condition_parameters) or {}
        condition = Condition(verb=condition_verb, parameters=parameters)
        action = Action(channel=channel.upper(), recipient=recipient, include_image=include_image)

        webhook_actions = None
        if webhook_url:
            payload_template = None
            if webhook_payload_template is not None:
                payload_template = PayloadTemplate(
                    template=webhook_payload_template,
                    headers=dict(webhook_headers or {}),
                )
            webhook_actions = [
                WebhookAction(
                    url=webhook_url,
                    include_image=webhook_include_image,
                    payload_template=payload_template,
                )
            ]

        return self.create_alert(
            detector,
            name,
            condition,
            actions=[action],
            webhook_actions=webhook_actions,
        )

    def create_note(
        self,
        detector: Detector | str,
        note: str,
        *,
        image: ImageArg | None = None,
        metadata: Mapping[str, Any] | str | None = None,
    ) -> dict[str, Any]:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")

        data = {"note": note}
        serialized_metadata = _dump_metadata(metadata) if metadata is not None else None
        if serialized_metadata is not None:
            data["metadata"] = serialized_metadata

        files = None
        if image is not None:
            payload = to_jpeg_bytes(image)
            files = {"image": ("note.jpg", payload, "image/jpeg")}

        return self._sync_http().post_json(f"/v1/detectors/{detector_id}/notes", data=data, files=files)

    def delete_all_rules(self, detector: Detector | str) -> int:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        payload = self._sync_http().delete("/v1/rules", params={"detector_id": detector_id})
        if isinstance(payload, Mapping) and "deleted" in payload:
            return int(payload["deleted"])
        return 0

    def make_generic_api_request(
        self,
        *,
        endpoint: str,
        method: str,
        headers: Mapping[str, str] | None = None,
        body: Any | None = None,
        data: Any | None = None,
    ) -> HTTPResponse:
        http_method = method.upper()
        request_kwargs: dict[str, Any] = {"headers": headers}
        if body is not None:
            request_kwargs["json"] = body
        if data is not None:
            request_kwargs["data"] = data

        response = self._sync_http().request_raw(http_method, endpoint, **request_kwargs)
        parsed = _maybe_parse_json(response)
        return HTTPResponse(status_code=response.status_code, headers=dict(response.headers), body=parsed)

    def download_mlbinary(self, detector: Detector | str, output_dir: str | os.PathLike[str]) -> None:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")

        response = self._sync_http().request_raw("GET", f"/v1/detectors/{detector_id}/mlbinary")
        filename = _extract_filename(response.headers)
        directory = Path(output_dir)
        directory.mkdir(parents=True, exist_ok=True)
        directory.joinpath(filename).write_bytes(response.content or b"")

