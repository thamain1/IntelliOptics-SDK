"""Pydantic models exposed as part of the public SDK surface."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence

from pydantic import BaseModel, Field

try:  # pragma: no cover - pydantic v2
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - pydantic v1 fallback
    ConfigDict = None  # type: ignore[assignment]


class _BaseModel(BaseModel):
    """Base model that allows unknown fields for forward compatibility."""

    if ConfigDict is not None:  # pragma: no branch
        model_config = ConfigDict(extra="allow")  # type: ignore[attr-defined]
    else:  # pragma: no cover - executed on pydantic v1
        class Config:
            extra = "allow"


class ModeEnum(str, Enum):
    BINARY = "BINARY"
    MULTICLASS = "MULTICLASS"
    COUNTING = "COUNTING"
    TEXT = "TEXT"
    BOUNDING_BOX = "BOUNDING_BOX"


class DetectorTypeEnum(str, Enum):
    DETECTOR = "DETECTOR"
    EDGE = "EDGE"


class StatusEnum(str, Enum):
    ACTIVE = "ACTIVE"
    DISABLED = "DISABLED"
    PAUSED = "PAUSED"
    DELETED = "DELETED"


class BlankEnum(str, Enum):
    BLANK = ""


class ResultTypeEnum(str, Enum):
    BINARY = "BINARY"
    COUNTING = "COUNTING"
    MULTICLASS = "MULTICLASS"
    TEXT = "TEXT"
    BOUNDING_BOX = "BOUNDING_BOX"


class ImageQueryTypeEnum(str, Enum):
    IMAGE_QUERY = "IMAGE_QUERY"


class ChannelEnum(str, Enum):
    EMAIL = "EMAIL"
    TEXT = "TEXT"


class SnoozeTimeUnitEnum(str, Enum):
    SECONDS = "SECONDS"
    MINUTES = "MINUTES"
    HOURS = "HOURS"
    DAYS = "DAYS"


class ROI(_BaseModel):
    label: str
    top_left: Sequence[float]
    bottom_right: Sequence[float]
    confidence: Optional[float] = None


class BinaryClassificationResult(_BaseModel):
    label: Optional[str] = None
    confidence: Optional[float] = None
    source: Optional[str] = None
    human_reviewed: Optional[bool] = None
    extra: Dict[str, Any] | None = None


class CountingResult(_BaseModel):
    label: Optional[str] = None
    count: Optional[int] = None
    confidence: Optional[float] = None
    extra: Dict[str, Any] | None = None


class MultiClassificationResult(_BaseModel):
    label: Optional[str] = None
    confidence: Optional[float] = None
    probabilities: Dict[str, float] | None = None


class TextRecognitionResult(_BaseModel):
    text: Optional[str] = None
    confidence: Optional[float] = None
    spans: List[Dict[str, Any]] | None = None


class BoundingBoxResult(_BaseModel):
    label: Optional[str] = None
    confidence: Optional[float] = None
    rois: List[ROI] | None = None


class Detector(_BaseModel):
    id: str
    name: str
    query: str
    group_name: Optional[str] = None
    mode: ModeEnum | str
    confidence_threshold: Optional[float] = Field(default=0.9, ge=0.0, le=1.0)
    patience_time: Optional[float] = Field(default=30.0, ge=0.0, le=3600.0)
    metadata: Optional[Dict[str, Any]] = None
    mode_configuration: Optional[Dict[str, Any]] = None
    escalation_type: Optional[str] = None
    status: StatusEnum | BlankEnum | None = None
    type: DetectorTypeEnum | str = DetectorTypeEnum.DETECTOR
    created_at: Optional[datetime] = None


class DetectorGroup(_BaseModel):
    id: str
    name: str
    description: Optional[str] = None


class PaginatedDetectorList(_BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[Detector] = Field(default_factory=list)


class ImageQuery(_BaseModel):
    id: str
    detector_id: Optional[str] = None
    confidence_threshold: Optional[float] = Field(default=0.9)
    patience_time: Optional[float] = Field(default=30.0, ge=0.0, le=3600.0)
    created_at: Optional[datetime] = None
    done_processing: Optional[bool] = False
    metadata: Optional[Dict[str, Any]] = None
    query: Optional[str] = None
    result: (
        BinaryClassificationResult
        | CountingResult
        | MultiClassificationResult
        | TextRecognitionResult
        | BoundingBoxResult
        | None
    ) = None
    result_type: ResultTypeEnum | str | None = None
    rois: List[ROI] | None = None
    text: Optional[str] = None
    type: ImageQueryTypeEnum | str | None = ImageQueryTypeEnum.IMAGE_QUERY
    status: str = "PENDING"


class PaginatedImageQueryList(_BaseModel):
    count: int
    next: Optional[str] = None
    previous: Optional[str] = None
    results: List[ImageQuery] = Field(default_factory=list)


class QueryResult(_BaseModel):
    id: str
    status: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    result_type: ResultTypeEnum | str | None = None
    extra: Optional[Dict[str, Any]] = None


class UserIdentity(_BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    tenant: Optional[str] = None
    roles: List[str] = Field(default_factory=list)


class FeedbackIn(_BaseModel):
    image_query_id: str
    correct_label: str
    notes: Optional[str] = None
    bboxes: Optional[List[Mapping[str, Any]]] = None


class Condition(_BaseModel):
    verb: str
    parameters: Mapping[str, Any] = Field(default_factory=dict)


class Action(_BaseModel):
    channel: ChannelEnum | str
    recipient: str
    include_image: bool = False


class ActionList(_BaseModel):
    items: List[Action] = Field(default_factory=list)

    def __iter__(self) -> Iterable[Action]:  # pragma: no cover - iteration helper
        return iter(self.items)


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
    snooze_time_unit: SnoozeTimeUnitEnum | str = SnoozeTimeUnitEnum.DAYS
    human_review_required: bool = False
    condition: Condition
    action: Action | ActionList | None = None
    webhook_action: List[WebhookAction] | None = None


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

