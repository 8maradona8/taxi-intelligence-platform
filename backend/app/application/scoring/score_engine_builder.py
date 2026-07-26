from collections.abc import Iterable

from app.application.scoring.aggregator import (
    ScoreAggregator,
)
from app.application.scoring.base_score_engine import (
    BaseScoreEngine,
)
from app.application.scoring.contributor import (
    ScoreContributor,
)
from app.application.scoring.score_registry import (
    ScoreRegistry,
)
from app.application.scoring.weighted_score_aggregator import (
    WeightedScoreAggregator,
)


class ScoreEngineBuilder:
    """Build a BaseScoreEngine from registered contributors."""

    def __init__(
        self,
        *,
        registry: ScoreRegistry | None = None,
        aggregator: ScoreAggregator | None = None,
    ) -> None:
        self._registry = registry or ScoreRegistry()
        self._aggregator = (
            aggregator if aggregator is not None else WeightedScoreAggregator()
        )

    @property
    def registry(self) -> ScoreRegistry:
        """Return the builder's current immutable registry."""
        return self._registry

    @property
    def aggregator(self) -> ScoreAggregator:
        """Return the configured aggregator."""
        return self._aggregator

    def add(
        self,
        contributor: ScoreContributor,
    ) -> "ScoreEngineBuilder":
        """Register one contributor."""
        self._registry = self._registry.register(contributor)
        return self

    def add_many(
        self,
        contributors: Iterable[ScoreContributor],
    ) -> "ScoreEngineBuilder":
        """Register multiple contributors."""
        self._registry = self._registry.extend(contributors)
        return self

    def with_aggregator(
        self,
        aggregator: ScoreAggregator,
    ) -> "ScoreEngineBuilder":
        """Replace the configured aggregator."""
        self._aggregator = aggregator
        return self

    def build(self) -> BaseScoreEngine:
        """Build a score engine from the current configuration."""
        return BaseScoreEngine(
            contributors=self._registry.contributors,
            aggregator=self._aggregator,
        )
