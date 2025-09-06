from dataclasses import dataclass
from typing import Literal, Optional

AnswerLabel = Literal["YES", "NO", "COUNT", "UNCLEAR"]

@dataclass
class Answer:
    answer: AnswerLabel
    confidence: float
    id: str
    latency_ms: Optional[int] = None
    model_version: Optional[str] = None

@dataclass
class Detector:
    id: str
    name: str
    mode: Literal["binary", "count", "custom"]
    query_text: str
    threshold: float
    status: str = "active"
