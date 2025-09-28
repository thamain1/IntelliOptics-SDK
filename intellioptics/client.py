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
from .errors import ApiTokenError, ExperimentalFeatureUnavailable, IntelliOpticsClientError
from .models import (
    Action,
    ActionList,
    ChannelEnum,
    Condition,
    Detector,
    DetectorGroup,
    FeedbackIn,
    HTTPResponse,
    ImageQuery,
    ModeEnum,
    PaginatedDetectorList,
    PaginatedImageQueryList,
    PayloadTemplate,
    ROI,
    QueryResult,
    Rule,
    SnoozeTimeUnitEnum,
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
    wait: bool | float | None,
    patience_time: float | None,
    confidence_threshold: float | None,
    human_review: str | None,
    metadata: Mapping[str, Any] | str | None,
    inspection_id: str | None,
    image_query_id: str | None,
    want_async: bool,
    request_timeout: float | None,
) -> tuple[dict[str, Any], dict[str, tuple[str, bytes, str]] | None]:
    detector_id = _detector_identifier(detector)
    form: dict[str, Any] = {
        "detector_id": detector_id,
        "wait": _serialize_wait(wait),
        "patience_time": patience_time,
        "confidence_threshold": confidence_threshold,
        "human_review": human_review,
        "metadata": _dump_metadata(metadata),
        "inspection_id": inspection_id,
        "image_query_id": image_query_id,
        "want_async": "true" if want_async else None,
        "request_timeout": request_timeout,
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

    label = payload.get("label") or result_block.get("label") or payload.get("answer")
    confidence = payload.get("confidence", result_block.get("confidence"))

    result: dict[str, Any] = dict(result_block)
    if label is not None:
        result.setdefault("label", label)
    if confidence is not None:
        result.setdefault("confidence", confidence)

    if "count" not in result and payload.get("count") is not None:
        result["count"] = payload["count"]

    extra: dict[str, Any] = {}
    raw_extra = payload.get("extra")
    if isinstance(raw_extra, Mapping):
        extra.update(raw_extra)

    for key in ("latency_ms", "model_version", "done_processing"):
        value = payload.get(key)
        if value is not None:
            extra.setdefault(key, value)

    for key, value in result.items():
        if key not in {"label", "confidence", "count"} and isinstance(value, Mapping):
            # nested mappings are included as-is; skip copying to extra
            continue

    if extra:
        existing_extra = result.get("extra")
        if isinstance(existing_extra, Mapping):
            merged = dict(existing_extra)
            merged.update(extra)
            result["extra"] = merged
        else:
            result["extra"] = extra

    metadata = payload.get("metadata")
    if isinstance(metadata, str):
        try:
            metadata = json.loads(metadata)
        except Exception:  # pragma: no cover - defensive
            pass

    rois = payload.get("rois")
    if not isinstance(rois, Iterable):
        rois = None

    confidence_threshold = payload.get("confidence_threshold")
    if confidence_threshold is None:
        confidence_threshold = 0.9

    patience_time = payload.get("patience_time")
    if patience_time is None:
        patience_time = 30.0

    done_processing = payload.get("done_processing")
    if done_processing is None:
        done_processing = False

    data: dict[str, Any] = {
        "id": payload.get("id") or payload.get("image_query_id"),
        "detector_id": payload.get("detector_id"),
        "confidence_threshold": confidence_threshold,
        "patience_time": patience_time,
        "created_at": payload.get("created_at"),
        "done_processing": done_processing,
        "metadata": metadata,
        "query": payload.get("query") or payload.get("prompt"),
        "result": result or None,
        "result_type": payload.get("result_type"),
        "rois": list(rois) if rois is not None else None,
        "text": payload.get("text"),
        "type": payload.get("type"),
        "status": _resolve_status(payload),
    }

    return {key: value for key, value in data.items() if value is not None or key == "status"}


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

    def create_detector(
        self,
        name: str,
        query: str,
        *,
        mode: ModeEnum | str = ModeEnum.BINARY,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        class_names: Sequence[str] | str | None = None,
        mode_configuration: Mapping[str, Any] | None = None,
    ) -> Detector:
        payload: dict[str, Any] = {
            "name": name,
            "query": query,
            "mode": mode.value if isinstance(mode, ModeEnum) else mode,
            "group_name": group_name,
            "confidence_threshold": confidence_threshold,
            "patience_time": patience_time,
            "pipeline_config": pipeline_config,
            "metadata": _dump_metadata(metadata),
            "mode_configuration": dict(mode_configuration) if mode_configuration else None,
        }

        if class_names is not None:
            if isinstance(class_names, str):
                payload["class_names"] = [class_names]
            else:
                payload["class_names"] = list(class_names)

        serialized = {key: value for key, value in payload.items() if value is not None}
        data = self._http.post_json("/v1/detectors", json=serialized)
        return Detector(**data)

    def list_detectors(self, page: int = 1, page_size: int = 10) -> PaginatedDetectorList:
        params = {"page": page, "page_size": page_size}
        payload = self._http.get_json("/v1/detectors", params=params)

        if not isinstance(payload, Mapping):
            items = payload if isinstance(payload, Sequence) else []
            payload = {"count": len(items), "results": items, "next": None, "previous": None}

        items = payload.get("results")
        if not isinstance(items, Sequence):
            items = payload.get("items")
        if not isinstance(items, Sequence):
            items = []

        data = {
            "count": payload.get("count", len(items)),
            "next": payload.get("next"),
            "previous": payload.get("previous"),
            "results": list(items),
        }
        return PaginatedDetectorList(**data)

    def create_binary_detector(
        self,
        name: str,
        query: str,
        *,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
    ) -> Detector:
        return self.create_detector(
            name,
            query,
            mode=ModeEnum.BINARY,
            group_name=group_name,
            confidence_threshold=confidence_threshold,
            patience_time=patience_time,
            pipeline_config=pipeline_config,
            metadata=metadata,
        )

    def create_multiclass_detector(
        self,
        name: str,
        query: str,
        class_names: Sequence[str],
        *,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
    ) -> Detector:
        return self.create_detector(
            name,
            query,
            mode=ModeEnum.MULTICLASS,
            group_name=group_name,
            confidence_threshold=confidence_threshold,
            patience_time=patience_time,
            pipeline_config=pipeline_config,
            metadata=metadata,
            class_names=class_names,
        )

    def create_counting_detector(
        self,
        name: str,
        query: str,
        class_name: str,
        *,
        max_count: int | None = None,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
    ) -> Detector:
        mode_config = {"class_name": class_name}
        if max_count is not None:
            mode_config["max_count"] = max_count
        return self.create_detector(
            name,
            query,
            mode=ModeEnum.COUNTING,
            group_name=group_name,
            confidence_threshold=confidence_threshold,
            patience_time=patience_time,
            pipeline_config=pipeline_config,
            metadata=metadata,
            class_names=[class_name],
            mode_configuration=mode_config,
        )

    def create_detector_group(self, name: str, description: str | None = None) -> DetectorGroup:
        payload = {"name": name, "description": description}
        serialized = {key: value for key, value in payload.items() if value is not None}
        response = self._http.post_json("/v1/detector-groups", json=serialized)
        return DetectorGroup(**response)

    def list_detector_groups(self) -> list[DetectorGroup]:
        payload = self._http.get_json("/v1/detector-groups")
        groups = payload if isinstance(payload, Sequence) else payload.get("results") if isinstance(payload, Mapping) else []
        if not isinstance(groups, Sequence):
            groups = []
        return [DetectorGroup(**group) for group in groups]

    def delete_detector(self, detector: Detector | str) -> None:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        self._http.delete(f"/v1/detectors/{detector_id}")

    def create_roi(
        self,
        label: str,
        top_left: Sequence[float],
        bottom_right: Sequence[float],
    ) -> ROI:
        return ROI(label=label, top_left=tuple(top_left), bottom_right=tuple(bottom_right))

    def get_detector_by_name(self, name: str) -> Detector:
        page = 1
        while True:
            detectors = self.list_detectors(page=page, page_size=50)
            for detector in detectors.results:
                if detector.name == name:
                    return detector
            if not detectors.next:
                break
            page += 1
        raise IntelliOpticsClientError(f"Detector named '{name}' was not found")

    def get_or_create_detector(
        self,
        name: str,
        query: str,
        *,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
    ) -> Detector:
        try:
            existing = self.get_detector_by_name(name)
        except IntelliOpticsClientError:
            existing = None

        if existing is not None:
            mismatches: list[str] = []
            if existing.query != query:
                mismatches.append("query")
            if group_name is not None and existing.group_name != group_name:
                mismatches.append("group_name")
            if confidence_threshold is not None and existing.confidence_threshold != confidence_threshold:
                mismatches.append("confidence_threshold")
            if metadata is not None and existing.metadata != metadata:
                mismatches.append("metadata")
            if mismatches:
                details = ", ".join(mismatches)
                raise ValueError(f"Existing detector has different configuration for: {details}")
            return existing

        return self.create_detector(
            name,
            query,
            group_name=group_name,
            confidence_threshold=confidence_threshold,
            pipeline_config=pipeline_config,
            metadata=metadata,
        )

    def get_detector(self, detector_id: str) -> Detector:
        payload = self._http.get_json(f"/v1/detectors/{detector_id}")
        return Detector(**payload)

    def submit_image_query(
        self,
        detector: Detector | str | None = None,
        image: ImageArg | None = None,
        *,
        wait: float | None = 30.0,
        patience_time: float | None = None,
        confidence_threshold: float | None = None,
        human_review: str | None = None,
        want_async: bool = False,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
        image_query_id: str | None = None,
        request_timeout: float | None = None,
    ) -> ImageQuery:
        if want_async and wait not in (0, 0.0, False, None):
            raise ValueError("wait must be 0 when want_async=True")

        form, files = _build_image_query_request(
            detector,
            image,
            wait=wait,
            patience_time=patience_time,
            confidence_threshold=confidence_threshold,
            human_review=human_review,
            metadata=metadata,
            inspection_id=inspection_id,
            image_query_id=image_query_id,
            want_async=want_async,
            request_timeout=request_timeout,
        )
        payload = self._http.post_json("/v1/image-queries", data=form, files=files)
        return ImageQuery(**_normalize_image_query_payload(payload))

    def submit_image_query_json(
        self,
        detector: Detector | str | None = None,
        *,
        image: str | None = None,
        wait: float | None = 30.0,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        human_review: str | None = None,
        want_async: bool = False,
        metadata: Mapping[str, Any] | None = None,
        inspection_id: str | None = None,
        image_query_id: str | None = None,
        request_timeout: float | None = None,
    ) -> ImageQuery:
        detector_id = _detector_identifier(detector)
        payload: dict[str, Any] = {
            "detector_id": detector_id,
            "image": image,
            "wait": wait,
            "confidence_threshold": confidence_threshold,
            "patience_time": patience_time,
            "human_review": human_review,
            "metadata": dict(metadata) if isinstance(metadata, Mapping) else metadata,
            "inspection_id": inspection_id,
            "image_query_id": image_query_id,
            "want_async": want_async,
            "request_timeout": request_timeout,
        }
        serialized = {key: value for key, value in payload.items() if value is not None}
        response = self._http.post_json("/v1/image-queries-json", json=serialized)
        return ImageQuery(**_normalize_image_query_payload(response))

    def get_image_query(self, image_query_id: str) -> ImageQuery:
        payload = self._http.get_json(f"/v1/image-queries/{image_query_id}")
        return ImageQuery(**_normalize_image_query_payload(payload))

    def get_image(self, image_query_id: str) -> bytes:
        response = self._http.request_raw("GET", f"/v1/image-queries/{image_query_id}/image")
        return response.content or b""

    def list_image_queries(
        self,
        *,
        page: int = 1,
        page_size: int = 10,
        detector_id: str | None = None,
    ) -> PaginatedImageQueryList:
        params = {"page": page, "page_size": page_size, "detector_id": detector_id}
        params = {key: value for key, value in params.items() if value is not None}
        payload = self._http.get_json("/v1/image-queries", params=params or None)

        if not isinstance(payload, Mapping):
            items = _coerce_image_query_items(payload)
            payload = {"count": len(items), "results": items, "next": None, "previous": None}

        raw_items = payload.get("results")
        if not isinstance(raw_items, Iterable):
            raw_items = _coerce_image_query_items(payload)

        normalized_items = [
            ImageQuery(**_normalize_image_query_payload(item)) for item in _coerce_image_query_items(raw_items)
        ]

        data = {
            "count": payload.get("count", len(normalized_items)),
            "next": payload.get("next"),
            "previous": payload.get("previous"),
            "results": normalized_items,
        }
        return PaginatedImageQueryList(**data)

    def get_result(self, image_query_id: str) -> QueryResult:
        payload = self._http.get_json(f"/v1/image-queries/{image_query_id}")
        normalized = _normalize_image_query_payload(payload)
        result_block = normalized.get("result")
        if not isinstance(result_block, Mapping):
            result_block = {}

        extra: dict[str, Any] = {}
        raw_extra = result_block.get("extra")
        if isinstance(raw_extra, Mapping):
            extra.update(raw_extra)

        for key, value in result_block.items():
            if key not in {"label", "confidence", "extra"} and value is not None:
                extra.setdefault(key, value)

        detector_id = normalized.get("detector_id")
        if detector_id is not None:
            extra.setdefault("detector_id", detector_id)

        return QueryResult(
            id=normalized.get("id", image_query_id),
            status=normalized.get("status", "PENDING"),
            label=result_block.get("label"),
            confidence=result_block.get("confidence"),
            result_type=normalized.get("result_type"),
            extra=extra or None,
        )

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
        image_query: ImageQuery | str,
        label: Union[str, int],
        rois: Sequence[ROI] | str | None = None,
    ) -> None:
        image_query_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        if not isinstance(image_query_id, str):
            raise TypeError("image_query must be an ImageQuery or string id")

        if hasattr(label, "value"):
            value = getattr(label, "value")
        else:
            value = label
        label_value = str(value)

        payload: dict[str, Any] = {
            "image_query_id": image_query_id,
            "label": label_value,
        }

        if rois is not None:
            if isinstance(rois, str):
                payload["rois"] = rois
            else:
                payload["rois"] = [
                    _serialize_model(roi) if hasattr(roi, "model_dump") or hasattr(roi, "dict") else dict(roi)
                    for roi in rois
                ]

        self._http.post_json("/v1/labels", json=payload)

    def start_inspection(self) -> str:
        response = self._http.post_json("/v1/inspections", json={})
        if isinstance(response, Mapping):
            for key in ("id", "inspection_id", "result"):
                value = response.get(key)
                if isinstance(value, str):
                    return value
        if isinstance(response, str):
            return response
        return str(response)

    def stop_inspection(self, inspection_id: str) -> str:
        response = self._http.post_json(f"/v1/inspections/{inspection_id}/stop", json={})
        if isinstance(response, Mapping):
            for key in ("status", "result"):
                value = response.get(key)
                if isinstance(value, str):
                    return value
        if isinstance(response, str):
            return response
        return str(response)

    def update_inspection_metadata(
        self,
        inspection_id: str,
        user_provided_key: str,
        user_provided_value: str,
    ) -> None:
        payload = {
            "user_provided_key": user_provided_key,
            "user_provided_value": user_provided_value,
        }
        self._http.post_json(f"/v1/inspections/{inspection_id}/metadata", json=payload)

    def update_detector_confidence_threshold(
        self,
        detector: Detector | str,
        confidence_threshold: float,
    ) -> None:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        self._http.patch_json(
            f"/v1/detectors/{detector_id}",
            json={"confidence_threshold": confidence_threshold},
        )

    def update_detector_escalation_type(
        self,
        detector: Detector | str,
        escalation_type: str,
    ) -> None:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        allowed = {"STANDARD", "NO_HUMAN_LABELING"}
        escalation = escalation_type.upper()
        if escalation not in allowed:
            raise ValueError("escalation_type must be STANDARD or NO_HUMAN_LABELING")
        self._http.patch_json(
            f"/v1/detectors/{detector_id}",
            json={"escalation_type": escalation},
        )

    def update_detector_status(
        self,
        detector: Detector | str,
        enabled: bool,
    ) -> None:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        self._http.patch_json(
            f"/v1/detectors/{detector_id}",
            json={"enabled": bool(enabled)},
        )

    # ------------------------------------------------------------------
    # Convenience helpers
    # ------------------------------------------------------------------
    def ask_ml(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        wait: float | None = 30.0,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
    ) -> ImageQuery:
        return self.submit_image_query(
            detector=detector,
            image=image,
            wait=wait,
            metadata=metadata,
            inspection_id=inspection_id,
        )

    def ask_async(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        patience_time: float | None = None,
        confidence_threshold: float | None = None,
        human_review: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
    ) -> ImageQuery:
        return self.submit_image_query(
            detector=detector,
            image=image,
            wait=0.0,
            patience_time=patience_time,
            confidence_threshold=confidence_threshold,
            human_review=human_review,
            metadata=metadata,
            inspection_id=inspection_id,
            want_async=True,
        )

    def ask_confident(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        confidence_threshold: float | None = None,
        wait: float | None = 30.0,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
        timeout_sec: float | None = None,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query = self.submit_image_query(
            detector=detector,
            image=image,
            wait=wait,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
        )

        threshold = confidence_threshold if confidence_threshold is not None else query.confidence_threshold or 0.9
        timeout = timeout_sec if timeout_sec is not None else (wait if wait is not None else 30.0)
        return self.wait_for_confident_result(
            query,
            confidence_threshold=threshold,
            timeout_sec=timeout,
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
            result = current.result
            result_confidence = getattr(result, "confidence", None)
            if current.status in {"DONE", "ERROR"}:
                if result is None or result_confidence is None or result_confidence >= confidence_threshold:
                    return current
            elif result_confidence is not None and result_confidence >= confidence_threshold:
                return current
            if time.time() >= deadline:
                return last_query
            time.sleep(poll_interval)

    def wait_for_ml_result(
        self,
        image_query: ImageQuery | str,
        *,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        deadline = time.time() + timeout_sec
        last_query: ImageQuery | None = None

        while True:
            current = self.get_image_query(query_id)
            last_query = current
            if current.result is not None:
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
        query: str,
        *,
        mode: ModeEnum | str = ModeEnum.BINARY,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        class_names: Sequence[str] | str | None = None,
        mode_configuration: Mapping[str, Any] | None = None,
    ) -> Detector:
        payload: dict[str, Any] = {
            "name": name,
            "query": query,
            "mode": mode.value if isinstance(mode, ModeEnum) else mode,
            "group_name": group_name,
            "confidence_threshold": confidence_threshold,
            "patience_time": patience_time,
            "pipeline_config": pipeline_config,
            "metadata": _dump_metadata(metadata),
            "mode_configuration": dict(mode_configuration) if mode_configuration else None,
        }
        if class_names is not None:
            payload["class_names"] = [class_names] if isinstance(class_names, str) else list(class_names)
        serialized = {key: value for key, value in payload.items() if value is not None}
        data = await self._http.post_json("/v1/detectors", json=serialized)
        return Detector(**data)

    async def list_detectors(self, page: int = 1, page_size: int = 10) -> PaginatedDetectorList:
        params = {"page": page, "page_size": page_size}
        payload = await self._http.get_json("/v1/detectors", params=params)

        if not isinstance(payload, Mapping):
            items = payload if isinstance(payload, Sequence) else []
            payload = {"count": len(items), "results": items, "next": None, "previous": None}

        items = payload.get("results")
        if not isinstance(items, Sequence):
            items = payload.get("items")
        if not isinstance(items, Sequence):
            items = []

        data = {
            "count": payload.get("count", len(items)),
            "next": payload.get("next"),
            "previous": payload.get("previous"),
            "results": list(items),
        }
        return PaginatedDetectorList(**data)

    async def get_detector(self, detector_id: str) -> Detector:
        payload = await self._http.get_json(f"/v1/detectors/{detector_id}")
        return Detector(**payload)

    async def submit_image_query(
        self,
        detector: Detector | str | None = None,
        image: ImageArg | None = None,
        *,
        wait: float | None = 30.0,
        patience_time: float | None = None,
        confidence_threshold: float | None = None,
        human_review: str | None = None,
        want_async: bool = False,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
        image_query_id: str | None = None,
        request_timeout: float | None = None,
    ) -> ImageQuery:
        if want_async and wait not in (0, 0.0, False, None):
            raise ValueError("wait must be 0 when want_async=True")

        form, files = _build_image_query_request(
            detector,
            image,
            wait=wait,
            patience_time=patience_time,
            confidence_threshold=confidence_threshold,
            human_review=human_review,
            metadata=metadata,
            inspection_id=inspection_id,
            image_query_id=image_query_id,
            want_async=want_async,
            request_timeout=request_timeout,
        )
        payload = await self._http.post_json("/v1/image-queries", data=form, files=files)
        return ImageQuery(**_normalize_image_query_payload(payload))

    async def submit_image_query_json(
        self,
        detector: Detector | str | None = None,
        *,
        image: str | None = None,
        wait: float | None = 30.0,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        human_review: str | None = None,
        want_async: bool = False,
        metadata: Mapping[str, Any] | None = None,
        inspection_id: str | None = None,
        image_query_id: str | None = None,
        request_timeout: float | None = None,
    ) -> ImageQuery:
        detector_id = _detector_identifier(detector)
        payload: dict[str, Any] = {
            "detector_id": detector_id,
            "image": image,
            "wait": wait,
            "confidence_threshold": confidence_threshold,
            "patience_time": patience_time,
            "human_review": human_review,
            "metadata": dict(metadata) if isinstance(metadata, Mapping) else metadata,
            "inspection_id": inspection_id,
            "image_query_id": image_query_id,
            "want_async": want_async,
            "request_timeout": request_timeout,
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
        page: int = 1,
        page_size: int = 10,
        detector_id: str | None = None,
    ) -> PaginatedImageQueryList:
        params = {"page": page, "page_size": page_size, "detector_id": detector_id}
        params = {key: value for key, value in params.items() if value is not None}
        payload = await self._http.get_json("/v1/image-queries", params=params or None)

        if not isinstance(payload, Mapping):
            items = _coerce_image_query_items(payload)
            payload = {"count": len(items), "results": items, "next": None, "previous": None}

        raw_items = payload.get("results")
        if not isinstance(raw_items, Iterable):
            raw_items = _coerce_image_query_items(payload)

        normalized_items = [
            ImageQuery(**_normalize_image_query_payload(item)) for item in _coerce_image_query_items(raw_items)
        ]

        data = {
            "count": payload.get("count", len(normalized_items)),
            "next": payload.get("next"),
            "previous": payload.get("previous"),
            "results": normalized_items,
        }
        return PaginatedImageQueryList(**data)

    async def get_result(self, image_query_id: str) -> QueryResult:
        payload = await self._http.get_json(f"/v1/image-queries/{image_query_id}")
        normalized = _normalize_image_query_payload(payload)
        result_block = normalized.get("result")
        if not isinstance(result_block, Mapping):
            result_block = {}

        extra: dict[str, Any] = {}
        raw_extra = result_block.get("extra")
        if isinstance(raw_extra, Mapping):
            extra.update(raw_extra)

        for key, value in result_block.items():
            if key not in {"label", "confidence", "extra"} and value is not None:
                extra.setdefault(key, value)

        detector_id = normalized.get("detector_id")
        if detector_id is not None:
            extra.setdefault("detector_id", detector_id)

        return QueryResult(
            id=normalized.get("id", image_query_id),
            status=normalized.get("status", "PENDING"),
            label=result_block.get("label"),
            confidence=result_block.get("confidence"),
            result_type=normalized.get("result_type"),
            extra=extra or None,
        )

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
        image_query: ImageQuery | str,
        label: Union[str, int],
        rois: Sequence[ROI] | str | None = None,
    ) -> None:
        image_query_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        if not isinstance(image_query_id, str):
            raise TypeError("image_query must be an ImageQuery or string id")

        if hasattr(label, "value"):
            value = getattr(label, "value")
        else:
            value = label
        label_value = str(value)

        payload: dict[str, Any] = {
            "image_query_id": image_query_id,
            "label": label_value,
        }

        if rois is not None:
            if isinstance(rois, str):
                payload["rois"] = rois
            else:
                payload["rois"] = [
                    _serialize_model(roi) if hasattr(roi, "model_dump") or hasattr(roi, "dict") else dict(roi)
                    for roi in rois
                ]

        await self._http.post_json("/v1/labels", json=payload)

    async def delete_image_query(self, image_query_id: str) -> None:
        await self._http.delete(f"/v1/image-queries/{image_query_id}")

    async def ask_ml(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        wait: float | None = 30.0,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
    ) -> ImageQuery:
        return await self.submit_image_query(
            detector=detector,
            image=image,
            wait=wait,
            metadata=metadata,
            inspection_id=inspection_id,
        )

    async def ask_async(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        patience_time: float | None = None,
        confidence_threshold: float | None = None,
        human_review: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
    ) -> ImageQuery:
        return await self.submit_image_query(
            detector=detector,
            image=image,
            wait=0.0,
            patience_time=patience_time,
            confidence_threshold=confidence_threshold,
            human_review=human_review,
            metadata=metadata,
            inspection_id=inspection_id,
            want_async=True,
        )

    async def ask_confident(
        self,
        detector: Detector | str,
        image: ImageArg,
        *,
        confidence_threshold: float | None = None,
        wait: float | None = 30.0,
        metadata: Mapping[str, Any] | str | None = None,
        inspection_id: str | None = None,
        timeout_sec: float | None = None,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query = await self.submit_image_query(
            detector=detector,
            image=image,
            wait=wait,
            confidence_threshold=confidence_threshold,
            metadata=metadata,
            inspection_id=inspection_id,
        )

        threshold = confidence_threshold if confidence_threshold is not None else query.confidence_threshold or 0.9
        timeout = timeout_sec if timeout_sec is not None else (wait if wait is not None else 30.0)
        return await self.wait_for_confident_result(
            query,
            confidence_threshold=threshold,
            timeout_sec=timeout,
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
            result = current.result
            result_confidence = getattr(result, "confidence", None)
            if current.status in {"DONE", "ERROR"}:
                if result is None or result_confidence is None or result_confidence >= confidence_threshold:
                    return current
            elif result_confidence is not None and result_confidence >= confidence_threshold:
                return current
            if time.time() >= deadline:
                return last_query
            await asyncio.sleep(poll_interval)

    async def wait_for_ml_result(
        self,
        image_query: ImageQuery | str,
        *,
        timeout_sec: float = 30.0,
        poll_interval: float = 0.5,
    ) -> ImageQuery:
        query_id = image_query.id if isinstance(image_query, ImageQuery) else image_query
        deadline = time.time() + timeout_sec
        last_query: ImageQuery | None = None

        while True:
            current = await self.get_image_query(query_id)
            last_query = current
            if current.result is not None:
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

    def _create_detector_via_api(self, payload: Mapping[str, Any]) -> Detector:
        response = self._sync_http().post_json("/v1/detectors", json={k: v for k, v in payload.items() if v is not None})
        return Detector(**response)

    def _create_detector(
        self,
        name: str,
        query: str,
        *,
        mode: ModeEnum | str,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
        class_names: Sequence[str] | str | None = None,
        mode_configuration: Mapping[str, Any] | None = None,
    ) -> Detector:
        if self._sync_client is not None:
            return self._sync_client.create_detector(
                name,
                query,
                mode=mode,
                group_name=group_name,
                confidence_threshold=confidence_threshold,
                patience_time=patience_time,
                pipeline_config=pipeline_config,
                metadata=metadata,
                class_names=class_names,
                mode_configuration=mode_configuration,
            )

        payload: dict[str, Any] = {
            "name": name,
            "query": query,
            "mode": mode.value if isinstance(mode, ModeEnum) else mode,
            "group_name": group_name,
            "confidence_threshold": confidence_threshold,
            "patience_time": patience_time,
            "pipeline_config": pipeline_config,
            "metadata": _dump_metadata(metadata),
            "mode_configuration": dict(mode_configuration) if mode_configuration else None,
        }
        if class_names is not None:
            payload["class_names"] = [class_names] if isinstance(class_names, str) else list(class_names)
        return self._create_detector_via_api(payload)

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
        rule_name: str,
        channel: str | ChannelEnum,
        recipient: str,
        *,
        alert_on: str = "CHANGED_TO",
        enabled: bool = True,
        include_image: bool = False,
        condition_parameters: Mapping[str, Any] | str | None = None,
        snooze_time_enabled: bool = False,
        snooze_time_value: int = 3600,
        snooze_time_unit: str = "SECONDS",
        human_review_required: bool = False,
    ) -> Rule:
        parameters = _parse_jsonish(condition_parameters)
        channel_value = channel.value if isinstance(channel, ChannelEnum) else str(channel).upper()
        condition = Condition(verb=alert_on.upper(), parameters=parameters or {})
        action = Action(channel=channel_value, recipient=recipient, include_image=include_image)

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
        metadata: Mapping[str, Any] | str | None = None,
    ) -> Detector:
        mode_config: dict[str, Any] = {"class_name": class_name}
        if max_num_bboxes is not None:
            mode_config["max_num_bboxes"] = max_num_bboxes
        return self._create_detector(
            name,
            query,
            mode=ModeEnum.BOUNDING_BOX,
            group_name=group_name,
            confidence_threshold=confidence_threshold,
            patience_time=patience_time,
            pipeline_config=pipeline_config,
            metadata=metadata,
            class_names=[class_name],
            mode_configuration=mode_config,
        )

    def create_text_recognition_detector(
        self,
        name: str,
        query: str,
        *,
        group_name: str | None = None,
        confidence_threshold: float | None = None,
        patience_time: float | None = None,
        pipeline_config: str | None = None,
        metadata: Mapping[str, Any] | str | None = None,
    ) -> Detector:
        return self._create_detector(
            name,
            query,
            mode=ModeEnum.TEXT,
            group_name=group_name,
            confidence_threshold=confidence_threshold,
            patience_time=patience_time,
            pipeline_config=pipeline_config,
            metadata=metadata,
        )

    def delete_all_rules(self, detector: Detector | str | None = None) -> int:
        params: dict[str, Any] | None = None
        if detector is not None:
            detector_id = _detector_identifier(detector)
            if detector_id is None:
                raise ValueError("detector is required")
            params = {"detector_id": detector_id}

        payload = self._sync_http().delete("/v1/rules", params=params)
        if isinstance(payload, Mapping) and "deleted" in payload:
            return int(payload["deleted"])
        return 0

    def delete_rule(self, action_id: int) -> None:
        self._sync_http().delete(f"/v1/rules/{action_id}")

    def make_generic_api_request(
        self,
        *,
        endpoint: str,
        method: str,
        headers: Mapping[str, str] | None = None,
        body: Any | None = None,
        files: Mapping[str, Any] | None = None,
        data: Any | None = None,
    ) -> HTTPResponse:
        http_method = method.upper()
        request_kwargs: dict[str, Any] = {"headers": headers}
        if body is not None:
            request_kwargs["json"] = body
        if files is not None:
            request_kwargs["files"] = files
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

    def get_detector_metrics(self, detector: Detector | str) -> dict:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        payload = self._sync_http().get_json(f"/v1/detectors/{detector_id}/metrics")
        return dict(payload)

    def get_detector_evaluation(self, detector: Detector | str) -> dict:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        payload = self._sync_http().get_json(f"/v1/detectors/{detector_id}/evaluation")
        return dict(payload)

    def get_notes(self, detector: Detector | str) -> Mapping[str, Any]:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        payload = self._sync_http().get_json(f"/v1/detectors/{detector_id}/notes")
        return payload if isinstance(payload, Mapping) else {}

    def get_raw_headers(self) -> Mapping[str, str]:
        return dict(self._sync_http().headers)

    def get_rule(self, action_id: int) -> Rule:
        payload = self._sync_http().get_json(f"/v1/rules/{action_id}")
        return Rule(**payload)

    def list_rules(self, page: int = 1, page_size: int = 10) -> PaginatedRuleList:
        params = {"page": page, "page_size": page_size}
        payload = self._sync_http().get_json("/v1/rules", params=params)
        if not isinstance(payload, Mapping):
            items = payload if isinstance(payload, Sequence) else []
            payload = {"count": len(items), "results": items, "next": None, "previous": None}
        return PaginatedRuleList(**payload)

    def make_action(self, channel: str, recipient: str, include_image: bool) -> Action:
        return Action(channel=channel.upper(), recipient=recipient, include_image=include_image)

    def make_condition(self, verb: str, parameters: dict) -> Condition:
        return Condition(verb=verb, parameters=parameters)

    def make_payload_template(self, template: str, headers: Mapping[str, str] | None = None) -> PayloadTemplate:
        return PayloadTemplate(template=template, headers=dict(headers) if headers else None)

    def make_webhook_action(
        self,
        url: str,
        include_image: bool,
        payload_template: PayloadTemplate | None = None,
    ) -> WebhookAction:
        return WebhookAction(url=url, include_image=include_image, payload_template=payload_template)

    def reset_detector(self, detector: Detector | str) -> None:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        self._sync_http().post_json(f"/v1/detectors/{detector_id}/reset")

    def update_detector_name(self, detector: Detector | str, name: str) -> None:
        detector_id = _detector_identifier(detector)
        if detector_id is None:
            raise ValueError("detector is required")
        self._sync_http().patch_json(f"/v1/detectors/{detector_id}", json={"name": name})

