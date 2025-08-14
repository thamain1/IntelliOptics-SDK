from dataclasses import dataclass
<<<<<<< HEAD
from typing import Optional, Dict
=======
from typing import Optional
>>>>>>> 5f1bbe5 (Initial commit of IntelliOptics SDK)

@dataclass
class Detector:
    id: str
    name: str
    query: str
    confidence_threshold: float

@dataclass
class ImageQuery:
    id: str
<<<<<<< HEAD
    result: Optional[Dict]
=======
    result: Optional[dict]
>>>>>>> 5f1bbe5 (Initial commit of IntelliOptics SDK)
    status: str
