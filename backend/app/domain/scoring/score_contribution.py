from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from app.domain.scoring.score_reason import (
    ScoreReason,
)


@dataclass(frozen=True)
class ScoreContribution:
    contributor: str
    score: float
    weight: float
    confidence: float
    reason: ScoreReason
    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        normalized_contributor = self.contributor.strip()

        if not normalized_contributor:
            raise ValueError("contributor cannot be empty")

        if not isfinite(self.score):
            raise ValueError("score must be finite")

        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be between 0.0 and 100.0")

        if not isfinite(self.weight):
            raise ValueError("weight must be finite")

        if self.weight <= 0.0:
            raise ValueError("weight must be greater than 0.0")

        if not isfinite(self.confidence):
            raise ValueError("confidence must be finite")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        object.__setattr__(
            self,
            "contributor",
            normalized_contributor,
        )

    @property
    def weighted_score(self) -> float:
        return self.score * self.weight

    @property
    def confidence_adjusted_weight(self) -> float:
        return self.weight * self.confidence
