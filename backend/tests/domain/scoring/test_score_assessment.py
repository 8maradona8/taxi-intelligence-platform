import pytest

from app.domain.scoring import (
    ScoreAssessment,
    ScoreContribution,
    ScoreLevel,
    ScoreReason,
)


def make_contribution() -> ScoreContribution:
    reason = ScoreReason(
        code="moderate_rain",
        description="Moderate rain increases demand",
        contribution=22.0,
    )

    return ScoreContribution(
        contributor="rain",
        score=80.0,
        weight=0.35,
        confidence=0.90,
        reason=reason,
    )


def test_score_assessment_create_derives_level_and_reasons() -> None:
    contribution = make_contribution()

    assessment = ScoreAssessment.create(
        score=81.234,
        confidence=0.93456,
        contributions=(contribution,),
    )

    assert assessment.score == 81.23
    assert assessment.confidence == 0.9346
    assert assessment.level == ScoreLevel.VERY_HIGH
    assert assessment.contributions == (contribution,)
    assert assessment.reasons == (contribution.reason,)


def test_score_assessment_create_clamps_values() -> None:
    assessment = ScoreAssessment.create(
        score=110.0,
        confidence=1.2,
    )

    assert assessment.score == 100.0
    assert assessment.confidence == 1.0
    assert assessment.level == ScoreLevel.VERY_HIGH


def test_score_assessment_rejects_mismatched_level() -> None:
    with pytest.raises(
        ValueError,
        match="level does not match",
    ):
        ScoreAssessment(
            score=85.0,
            confidence=0.90,
            level=ScoreLevel.LOW,
        )


@pytest.mark.parametrize(
    ("score", "confidence"),
    [
        (-0.01, 0.90),
        (100.01, 0.90),
        (50.0, -0.01),
        (50.0, 1.01),
    ],
)
def test_score_assessment_rejects_invalid_values(
    score: float,
    confidence: float,
) -> None:
    with pytest.raises(ValueError):
        ScoreAssessment(
            score=score,
            confidence=confidence,
            level=ScoreLevel.MEDIUM,
        )
