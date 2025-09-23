"""Pydantic models that mirror the IntelliOptics OpenAPI schema."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field

try:  # pragma: no cover - Pydantic v2
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - Pydantic v1 fallback
    ConfigDict = None  # type: ignore[assignment]


class _Model(BaseModel):
    if ConfigDict is not None:  # pragma: no cover - Pydantic v2 only branch
        model_config = ConfigDict(extra="forbid", populate_by_name=True)  # type: ignore[arg-type]
    else:  # pragma: no cover - executed on Pydantic v1
        class Config:
            allow_population_by_field_name = True
            extra = "forbid"

    # Compatibility helpers between Pydantic v1 and v2
    def to_dict(self, **kwargs: Any) -> Dict[str, Any]:
        if hasattr(self, "model_dump"):
            return self.model_dump(**kwargs)
        return self.dict(**kwargs)

    @classmethod
    def parse(cls, data: Any) -> "_Model":
        if hasattr(cls, "model_validate"):
            return cls.model_validate(data)  # type: ignore[attr-defined]
        return cls.parse_obj(data)


class DetectorMode(str, Enum):
    BINARY = "binary"
    COUNT = "count"
    CUSTOM = "custom"


class AnswerLabel(str, Enum):
    YES = "YES"
    NO = "NO"
    COUNT = "COUNT"
    UNCLEAR = "UNCLEAR"


class DetectorCreate(_Model):
    name: str
    mode: DetectorMode
    query_text: str = Field(alias="query_text")
    threshold: float = 0.75


class DetectorOut(_Model):
    id: str
    name: str
    mode: DetectorMode
    query_text: str = Field(alias="query_text")
    threshold: float
    status: str = "active"


class Answer(_Model):
    image_query_id: str
    answer: AnswerLabel
    confidence: float
    latency_ms: Optional[int] = None
    model_version: Optional[str] = Field(default="demo-v0")


class ImageQueryJson(_Model):
    detector_id: str
    image: Optional[str] = None
    wait: bool = True


class FeedbackIn(_Model):
    image_query_id: str
    correct_label: AnswerLabel
    bboxes: Optional[Sequence[Dict[str, Any]]] = None


class ValidationErrorItem(_Model):
    loc: List[Union[str, int]]
    msg: str
    type: str


class HTTPValidationError(_Model):
    detail: Optional[List[ValidationErrorItem]] = None


__all__ = [
    "Answer",
    "AnswerLabel",
    "DetectorCreate",
    "DetectorMode",
    "DetectorOut",
    "FeedbackIn",
    "HTTPValidationError",
    "ImageQueryJson",
    "ValidationErrorItem",
]
