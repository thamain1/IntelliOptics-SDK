"""Typed models used by the IntelliOptics SDK."""

from __future__ import annotations

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
