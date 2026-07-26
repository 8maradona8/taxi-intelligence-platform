import pytest

from app.domain.scoring import (
    ScoreContribution,
    ScoreReason,
)


def make_reason() -> ScoreReason:
    return ScoreReason(
        code="moderate_rain",
        description="Moderate rain increases demand",
        contribution=22.0,
    )


def test_score_contribution_calculates_weights() -> None:
    contribution = ScoreContribution(
        contributor=" rain ",
        score=80.0,
        weight=0.35,
        confidence=0.90,
        reason=make_reason(),
    )

    assert contribution.contributor == "rain"
    assert contribution.weighted_score == 28.0
    assert contribution.confidence_adjusted_weight == (pytest.approx(0.315))


@pytest.mark.parametrize(
    ("field_name", "field_value"),
    [
        ("score", -0.01),
        ("score", 100.01),
        ("weight", 0.0),
        ("weight", -1.0),
        ("confidence", -0.01),
        ("confidence", 1.01),
    ],
)
def test_score_contribution_rejects_invalid_values(
    field_name: str,
    field_value: float,
) -> None:
    values = {
        "contributor": "rain",
        "score": 80.0,
        "weight": 0.35,
        "confidence": 0.90,
        "reason": make_reason(),
    }
    values[field_name] = field_value

    with pytest.raises(ValueError):
        ScoreContribution(**values)


def test_score_contribution_rejects_empty_name() -> None:
    with pytest.raises(
        ValueError,
        match="contributor cannot be empty",
    ):
        ScoreContribution(
            contributor="   ",
            score=80.0,
            weight=0.35,
            confidence=0.90,
            reason=make_reason(),
        )
