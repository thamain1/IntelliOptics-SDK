from enum import Enum


class AnswerOutAnswer(str, Enum):
    COUNT = "COUNT"
    NO = "NO"
    UNCLEAR = "UNCLEAR"
    YES = "YES"

    def __str__(self) -> str:
        return str(self.value)
