import pytest

from app.application.scoring import (
    ScoreAggregator,
    WeightedScoreAggregator,
)
from app.domain.scoring import (
    ScoreContribution,
    ScoreLevel,
    ScoreReason,
)


def make_contribution(
    *,
    contributor: str,
    score: float,
    weight: float,
    confidence: float,
) -> ScoreContribution:
    return ScoreContribution(
        contributor=contributor,
        score=score,
        weight=weight,
        confidence=confidence,
        reason=ScoreReason(
            code=f"{contributor}_reason",
            description=(f"{contributor} contributed to the score"),
            contribution=score,
        ),
    )


def test_weighted_aggregator_satisfies_protocol() -> None:
    aggregator = WeightedScoreAggregator()

    assert isinstance(
        aggregator,
        ScoreAggregator,
    )


def test_single_contribution_preserves_score() -> None:
    contribution = make_contribution(
        contributor="weather",
        score=80.0,
        weight=0.35,
        confidence=0.90,
    )

    assessment = WeightedScoreAggregator().aggregate((contribution,))

    assert assessment.score == 80.0
    assert assessment.confidence == 0.90
    assert assessment.level == ScoreLevel.VERY_HIGH
    assert assessment.contributions == (contribution,)


def test_equal_weights_produce_arithmetic_average() -> None:
    first = make_contribution(
        contributor="weather",
        score=80.0,
        weight=0.50,
        confidence=1.0,
    )
    second = make_contribution(
        contributor="airport",
        score=60.0,
        weight=0.50,
        confidence=1.0,
    )

    assessment = WeightedScoreAggregator().aggregate(
        (
            first,
            second,
        )
    )

    assert assessment.score == 70.0
    assert assessment.confidence == 1.0
    assert assessment.level == ScoreLevel.HIGH


def test_configured_weights_change_final_score() -> None:
    high_weight = make_contribution(
        contributor="airport",
        score=90.0,
        weight=0.70,
        confidence=1.0,
    )
    low_weight = make_contribution(
        contributor="weather",
        score=30.0,
        weight=0.30,
        confidence=1.0,
    )

    assessment = WeightedScoreAggregator().aggregate(
        (
            high_weight,
            low_weight,
        )
    )

    assert assessment.score == 72.0
    assert assessment.confidence == 1.0


def test_low_confidence_reduces_contributor_influence() -> None:
    uncertain_high_score = make_contribution(
        contributor="airport",
        score=90.0,
        weight=0.50,
        confidence=0.20,
    )
    reliable_low_score = make_contribution(
        contributor="weather",
        score=30.0,
        weight=0.50,
        confidence=1.0,
    )

    assessment = WeightedScoreAggregator().aggregate(
        (
            uncertain_high_score,
            reliable_low_score,
        )
    )

    assert assessment.score == 40.0
    assert assessment.confidence == 0.60
    assert assessment.score < 60.0


def test_confidence_is_weighted_by_configured_weight() -> None:
    high_weight = make_contribution(
        contributor="airport",
        score=70.0,
        weight=0.80,
        confidence=0.90,
    )
    low_weight = make_contribution(
        contributor="weather",
        score=70.0,
        weight=0.20,
        confidence=0.40,
    )

    assessment = WeightedScoreAggregator().aggregate(
        (
            high_weight,
            low_weight,
        )
    )

    assert assessment.score == 70.0
    assert assessment.confidence == 0.80


def test_assessment_contains_all_reasons() -> None:
    weather = make_contribution(
        contributor="weather",
        score=80.0,
        weight=0.50,
        confidence=0.90,
    )
    airport = make_contribution(
        contributor="airport",
        score=60.0,
        weight=0.50,
        confidence=0.80,
    )

    assessment = WeightedScoreAggregator().aggregate(
        (
            weather,
            airport,
        )
    )

    assert assessment.reasons == (
        weather.reason,
        airport.reason,
    )


def test_assessment_contains_aggregation_metadata() -> None:
    weather = make_contribution(
        contributor="weather",
        score=80.0,
        weight=0.60,
        confidence=0.90,
    )
    airport = make_contribution(
        contributor="airport",
        score=60.0,
        weight=0.40,
        confidence=0.50,
    )

    assessment = WeightedScoreAggregator().aggregate(
        (
            weather,
            airport,
        )
    )

    assert assessment.metadata == {
        "aggregation_method": ("confidence_adjusted_weighted_average"),
        "contributors_count": 2,
        "total_weight": 1.0,
        "effective_weight": 0.74,
    }


def test_weights_do_not_need_to_sum_to_one() -> None:
    weather = make_contribution(
        contributor="weather",
        score=80.0,
        weight=3.0,
        confidence=1.0,
    )
    airport = make_contribution(
        contributor="airport",
        score=20.0,
        weight=1.0,
        confidence=1.0,
    )

    assessment = WeightedScoreAggregator().aggregate(
        (
            weather,
            airport,
        )
    )

    assert assessment.score == 65.0
    assert assessment.confidence == 1.0
    assert assessment.metadata["total_weight"] == 4.0


def test_empty_contributions_are_rejected() -> None:
    aggregator = WeightedScoreAggregator()

    with pytest.raises(
        ValueError,
        match="At least one score contribution",
    ):
        aggregator.aggregate(())


def test_zero_effective_weight_is_rejected() -> None:
    weather = make_contribution(
        contributor="weather",
        score=80.0,
        weight=0.50,
        confidence=0.0,
    )
    airport = make_contribution(
        contributor="airport",
        score=60.0,
        weight=0.50,
        confidence=0.0,
    )

    with pytest.raises(
        ValueError,
        match="positive confidence",
    ):
        WeightedScoreAggregator().aggregate(
            (
                weather,
                airport,
            )
        )
