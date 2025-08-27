from enum import Enum

class DetectorOutMode(str, Enum):
    BINARY = "binary"
    COUNT = "count"
    CUSTOM = "custom"

    def __str__(self) -> str:
        return str(self.value)
