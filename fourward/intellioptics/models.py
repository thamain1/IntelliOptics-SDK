from dataclasses import dataclass
from typing import Optional, Dict

@dataclass
class Detector:
    id: str
    name: str
    query: str
    confidence_threshold: float

@dataclass
class ImageQuery:
    id: str
    result: Optional[Dict]
    status: str
