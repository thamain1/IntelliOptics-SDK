from typing import Optional, List, Dict, Any, Literal

from pydantic import BaseModel

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


class FeedbackIn(BaseModel):
    image_query_id: str
    correct_label: Literal["YES", "NO", "COUNT", "UNCLEAR"]
    bboxes: Optional[List[Dict[str, Any]]] = None
