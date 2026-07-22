from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite
from typing import Any

from app.domain.scoring.score_contribution import (
    ScoreContribution,
)
from app.domain.scoring.score_level import ScoreLevel
from app.domain.scoring.score_reason import ScoreReason


@dataclass(frozen=True)
class ScoreAssessment:
    score: float
    confidence: float
    level: ScoreLevel
    contributions: tuple[ScoreContribution, ...] = ()
    reasons: tuple[ScoreReason, ...] = ()
    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        if not isfinite(self.score):
            raise ValueError("score must be finite")

        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be between 0.0 and 100.0")

        if not isfinite(self.confidence):
            raise ValueError("confidence must be finite")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        expected_level = ScoreLevel.from_score(self.score)

        if self.level != expected_level:
            raise ValueError("level does not match the supplied score")

    @classmethod
    def create(
        cls,
        *,
        score: float,
        confidence: float,
        contributions: tuple[
            ScoreContribution,
            ...,
        ] = (),
        reasons: tuple[ScoreReason, ...] | None = None,
        metadata: Mapping[str, Any] | None = None,
    ) -> "ScoreAssessment":
        normalized_score = round(
            min(100.0, max(0.0, score)),
            2,
        )
        normalized_confidence = round(
            min(1.0, max(0.0, confidence)),
            4,
        )

        assessment_reasons = (
            reasons
            if reasons is not None
            else tuple(contribution.reason for contribution in contributions)
        )

        return cls(
            score=normalized_score,
            confidence=normalized_confidence,
            level=ScoreLevel.from_score(normalized_score),
            contributions=contributions,
            reasons=assessment_reasons,
            metadata=metadata or {},
        )
