from typing import Protocol, runtime_checkable

from app.domain.scoring import (
    ScoreAssessment,
    ScoreContribution,
)


@runtime_checkable
class ScoreAggregator(Protocol):
    def aggregate(
        self,
        contributions: tuple[ScoreContribution, ...],
    ) -> ScoreAssessment:
        """Combine contributions into one assessment."""
        ...
