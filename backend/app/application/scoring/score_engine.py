from typing import Protocol, runtime_checkable

from app.domain.scoring import (
    ScoreAssessment,
    ScoreContext,
)


@runtime_checkable
class ScoreEngine(Protocol):
    def assess(
        self,
        context: ScoreContext,
    ) -> ScoreAssessment:
        """Produce a complete score assessment."""
        ...
