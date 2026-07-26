from enum import StrEnum


class ScoreLevel(StrEnum):
    VERY_LOW = "very_low"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    VERY_HIGH = "very_high"

    @classmethod
    def from_score(cls, score: float) -> "ScoreLevel":
        if not 0.0 <= score <= 100.0:
            raise ValueError("score must be between 0.0 and 100.0")

        if score < 20.0:
            return cls.VERY_LOW

        if score < 40.0:
            return cls.LOW

        if score < 60.0:
            return cls.MEDIUM

        if score < 80.0:
            return cls.HIGH

        return cls.VERY_HIGH
