from typing import Any, Optional
from pydantic import BaseModel, Field

class ImageQueryResult(BaseModel):
    label: Optional[str] = None
    confidence: Optional[float] = None
    count: Optional[int] = None
    extra: Optional[dict[str, Any]] = None

class ImageQuery(BaseModel):
    id: str
    status: str = Field(default="PROCESSING")   # PROCESSING | DONE | FAILED
    result_type: Optional[str] = None
    done_processing: bool = False
    result: Optional[ImageQueryResult] = None
