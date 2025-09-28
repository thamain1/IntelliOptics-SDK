"""Typed models used by the IntelliOptics SDK."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Mapping, Optional

from pydantic import BaseModel, Field

try:  # pragma: no cover - compatibility shim for pydantic v1
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover
    ConfigDict = None  # type: ignore[misc, assignment]


class _BaseModel(BaseModel):
    """Base class that allows extra fields across Pydantic versions."""

    if ConfigDict is not None:  # pragma: no branch - executed on Pydantic v2
        model_config = ConfigDict(extra="allow")  # type: ignore[attr-defined]
    else:  # pragma: no cover - executed on Pydantic v1
        class Config:
            extra = "allow"


class Detector(_BaseModel):
    id: str
    name: str
    mode: Optional[str] = None
    query_text: Optional[str] = None
    threshold: Optional[float] = None
    status: Optional[str] = None
    labels: List[str] = Field(default_factory=list)


class ImageQuery(_BaseModel):
    id: str
    detector_id: Optional[str] = None
    status: str = "PENDING"
    result_type: Optional[str] = None
    confidence: Optional[float] = None
    label: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class QueryResult(_BaseModel):
    id: str
    status: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    result_type: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None


class UserIdentity(_BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    tenant: Optional[str] = None
    roles: List[str] = Field(default_factory=list)


class FeedbackIn(_BaseModel):
    image_query_id: str
    correct_label: Literal["YES", "NO", "COUNT", "UNCLEAR"]
    bboxes: Optional[List[Mapping[str, Any]]] = None


SnoozeTimeUnit = Literal["SECONDS", "MINUTES", "HOURS", "DAYS"]
Channel = Literal["TEXT", "EMAIL"]


class Condition(_BaseModel):
    verb: str
    parameters: Mapping[str, Any]


class Action(_BaseModel):
    channel: Channel
    recipient: str
    include_image: bool


class PayloadTemplate(_BaseModel):
    template: str
    headers: Optional[Dict[str, str]] = None


class WebhookAction(_BaseModel):
    url: str
    include_image: Optional[bool] = None
    payload_template: Optional[PayloadTemplate] = None
    last_message_failed: Optional[bool] = None
    last_failure_error: Optional[str] = None
    last_failed_at: Optional[datetime] = None


class Rule(_BaseModel):
    id: int
    detector_id: str
    detector_name: str
    name: str
    enabled: bool = True
    snooze_time_enabled: bool = False
    snooze_time_value: int = 0
    snooze_time_unit: SnoozeTimeUnit = "DAYS"
    human_review_required: bool = False
    condition: Condition
    action: Optional[Action | List[Action]] = None
    webhook_action: Optional[List[WebhookAction]] = None


class PaginatedDetectorList(_BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Detector] = Field(default_factory=list)


class PaginatedImageQueryList(_BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[ImageQuery] = Field(default_factory=list)


class PaginatedRuleList(_BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Rule] = Field(default_factory=list)


@dataclass
class HTTPResponse:
    status_code: int
    headers: Mapping[str, str]
    body: Any
