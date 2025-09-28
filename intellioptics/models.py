
from typing import Optional, List, Dict, Any, Literal
from pydantic import BaseModel
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - Pydantic v1 compatibility
    ConfigDict = None  # type: ignore
from typing import Optional, List, Dict, Any

class Detector(BaseModel):
    id: str
    name: str
    mode: str
    query_text: str

    threshold: Optional[float] = None
    status: Optional[str] = None

    threshold: float
    status: Optional[str] = "active"
    labels: List[str] = Field(default_factory=list)


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


class FeedbackIn(BaseModel):
    image_query_id: str
    correct_label: Literal["YES", "NO", "COUNT", "UNCLEAR"]
    bboxes: Optional[List[Dict[str, Any]]] = None
class UserIdentity(BaseModel):
    id: str
    email: Optional[str] = None
    name: Optional[str] = None
    tenant: Optional[str] = None
    roles: List[str] = Field(default_factory=list)

    if ConfigDict is not None:  # pragma: no branch
        model_config = ConfigDict(extra="allow")  # type: ignore[attr-defined]
    else:  # pragma: no cover - executed on Pydantic v1
        class Config:
            extra = "allow"


class FeedbackIn(BaseModel):
    image_query_id: str
    correct_label: str
    bboxes: Optional[List[Dict[str, Any]]] = None

    if ConfigDict is not None:  # pragma: no branch
        model_config = ConfigDict(extra="allow")  # type: ignore[attr-defined]
    else:  # pragma: no cover - executed on Pydantic v1
        class Config:
            extra = "allow"
