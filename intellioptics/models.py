from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

try:  # pragma: no cover - pydantic v2
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - pydantic v1
    ConfigDict = None


class Identity(BaseModel):
    id: str
    name: Optional[str] = None
    email: Optional[str] = None
    roles: List[str] = Field(default_factory=list)
    metadata: Optional[Dict[str, Any]] = None

    if ConfigDict is not None:  # pragma: no branch
        model_config = ConfigDict(extra="allow")
    else:  # pragma: no cover - pydantic v1
        class Config:
            extra = "allow"

class Detector(BaseModel):
    id: str
    name: str
    labels: List[str] = []

class ImageQuery(BaseModel):
    id: str
    detector_id: Optional[str] = None
    status: str = "PENDING"
    result_type: Optional[str] = None
    confidence: Optional[float] = None
    label: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None

class QueryResult(BaseModel):
    id: str
    status: str
    label: Optional[str] = None
    confidence: Optional[float] = None
    result_type: Optional[str] = None
    extra: Optional[Dict[str, Any]] = None
