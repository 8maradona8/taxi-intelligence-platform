from typing import Protocol, runtime_checkable

from app.domain.scoring import (
    ScoreContext,
    ScoreContribution,
)


@runtime_checkable
class ScoreContributor(Protocol):
    @property
    def name(self) -> str:
        """Return the unique contributor name."""
        ...

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        """Evaluate one scoring factor."""
        ...
