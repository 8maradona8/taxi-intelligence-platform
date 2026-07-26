from app.application.scoring import ScoreAggregator
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContribution,
    ScoreReason,
)


class FakeScoreAggregator:
    def aggregate(
        self,
        contributions: tuple[ScoreContribution, ...],
    ) -> ScoreAssessment:
        total_weight = sum(contribution.weight for contribution in contributions)

        weighted_score = sum(
            contribution.weighted_score for contribution in contributions
        )

        score = weighted_score / total_weight

        confidence = sum(
            contribution.confidence for contribution in contributions
        ) / len(contributions)

        return ScoreAssessment.create(
            score=score,
            confidence=confidence,
            contributions=contributions,
        )


def make_contribution() -> ScoreContribution:
    return ScoreContribution(
        contributor="rain",
        score=80.0,
        weight=0.35,
        confidence=0.95,
        reason=ScoreReason(
            code="rain_detected",
            description=("Rain increases expected taxi demand"),
            contribution=80.0,
        ),
    )


def test_aggregator_satisfies_protocol() -> None:
    aggregator = FakeScoreAggregator()

    assert isinstance(
        aggregator,
        ScoreAggregator,
    )


def test_aggregator_returns_assessment() -> None:
    aggregator = FakeScoreAggregator()
    contribution = make_contribution()

    assessment = aggregator.aggregate((contribution,))

    assert assessment.score == 80.0
    assert assessment.confidence == 0.95
    assert assessment.contributions == (contribution,)
