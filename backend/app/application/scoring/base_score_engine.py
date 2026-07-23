from collections.abc import Iterable

from app.application.scoring.aggregator import ScoreAggregator
from app.application.scoring.contributor import ScoreContributor
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContext,
    ScoreContribution,
)


class BaseScoreEngine:
    """Coordinate score contributors and aggregate their results."""

    def __init__(
        self,
        *,
        contributors: Iterable[ScoreContributor],
        aggregator: ScoreAggregator,
    ) -> None:
        registered_contributors = tuple(contributors)

        if not registered_contributors:
            raise ValueError("At least one score contributor is required")

        self._validate_unique_contributor_names(registered_contributors)

        self._contributors = registered_contributors
        self._aggregator = aggregator

    @property
    def contributors(
        self,
    ) -> tuple[ScoreContributor, ...]:
        return self._contributors

    @property
    def aggregator(self) -> ScoreAggregator:
        return self._aggregator

    def assess(
        self,
        context: ScoreContext,
    ) -> ScoreAssessment:
        contributions = tuple(
            self._evaluate_contributor(
                contributor=contributor,
                context=context,
            )
            for contributor in self._contributors
        )

        return self._aggregator.aggregate(contributions)

    @staticmethod
    def _validate_unique_contributor_names(
        contributors: tuple[ScoreContributor, ...],
    ) -> None:
        seen_names: set[str] = set()
        duplicate_names: set[str] = set()

        for contributor in contributors:
            if contributor.name in seen_names:
                duplicate_names.add(contributor.name)

            seen_names.add(contributor.name)

        if duplicate_names:
            duplicates = ", ".join(sorted(duplicate_names))

            raise ValueError(f"Score contributor names must be unique: {duplicates}")

    @staticmethod
    def _evaluate_contributor(
        *,
        contributor: ScoreContributor,
        context: ScoreContext,
    ) -> ScoreContribution:
        contribution = contributor.evaluate(context)

        if contribution.contributor != contributor.name:
            raise ValueError(
                "Score contribution contributor name does "
                "not match registered contributor: "
                f"expected {contributor.name!r}, "
                f"received {contribution.contributor!r}"
            )

        return contribution
