from pydantic import BaseModel, Field
try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - Pydantic v1 compatibility
    ConfigDict = None  # type: ignore
from typing import Optional, Any

class Detector(BaseModel):
    id: str
    name: str
    labels: list[str] = Field(default_factory=list)

class ImageQuery(BaseModel):
    id: str
    detector_id: Optional[str] = None
    status: str = "PENDING"
    result_type: Optional[str] = None
    confidence: Optional[float] = None
    label: Optional[str] = None
    extra: Optional[dict[str, Any]] = None

class QueryResult(BaseModel):
    id: str
    status: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    result_type: Optional[str] = None
    extra: Optional[dict[str, Any]] = None


class UserIdentity(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    tenant: Optional[str] = None
    roles: list[str] = Field(default_factory=list)

    if ConfigDict is not None:  # pragma: no branch
        model_config = ConfigDict(extra="allow")  # type: ignore[attr-defined]
    else:  # pragma: no cover - executed on Pydantic v1
        class Config:
            extra = "allow"
