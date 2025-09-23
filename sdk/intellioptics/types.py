from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

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
    labels: List[str] = field(default_factory=list)
    status: str = "active"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    extra: Dict[str, Any] = field(default_factory=dict)
