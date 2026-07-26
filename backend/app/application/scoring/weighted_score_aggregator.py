from math import fsum

from app.application.scoring.aggregator import (
    ScoreAggregator,
)
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContribution,
)


class WeightedScoreAggregator:
    """Aggregate scores using confidence-adjusted weights.

    A contribution's influence on the final score is determined by:

        effective_weight = weight * confidence

    Aggregate confidence is calculated separately using the configured
    contributor weights, preventing confidence from being applied twice.
    """

    AGGREGATION_METHOD = "confidence_adjusted_weighted_average"

    def aggregate(
        self,
        contributions: tuple[ScoreContribution, ...],
    ) -> ScoreAssessment:
        if not contributions:
            raise ValueError("At least one score contribution is required")

        total_weight = fsum(contribution.weight for contribution in contributions)

        if total_weight <= 0.0:
            raise ValueError("Total contribution weight must be greater than 0.0")

        effective_weight = fsum(
            contribution.confidence_adjusted_weight for contribution in contributions
        )

        if effective_weight <= 0.0:
            raise ValueError("At least one contribution must have positive confidence")

        weighted_score = fsum(
            contribution.score * contribution.confidence_adjusted_weight
            for contribution in contributions
        )

        aggregate_score = weighted_score / effective_weight

        weighted_confidence = fsum(
            contribution.weight * contribution.confidence
            for contribution in contributions
        )

        aggregate_confidence = weighted_confidence / total_weight

        return ScoreAssessment.create(
            score=aggregate_score,
            confidence=aggregate_confidence,
            contributions=contributions,
            metadata={
                "aggregation_method": (self.AGGREGATION_METHOD),
                "contributors_count": len(contributions),
                "total_weight": round(
                    total_weight,
                    6,
                ),
                "effective_weight": round(
                    effective_weight,
                    6,
                ),
            },
        )


assert isinstance(
    WeightedScoreAggregator(),
    ScoreAggregator,
)
