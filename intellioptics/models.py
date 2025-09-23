from pydantic import BaseModel
from typing import Optional, Dict, Any

class Detector(BaseModel):
    id: str
    name: str
    mode: str
    query_text: str
    threshold: float
    status: Optional[str] = "active"

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
