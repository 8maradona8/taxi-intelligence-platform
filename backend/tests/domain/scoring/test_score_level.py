import pytest

from app.domain.scoring import ScoreLevel


@pytest.mark.parametrize(
    ("score", "expected_level"),
    [
        (0.0, ScoreLevel.VERY_LOW),
        (19.99, ScoreLevel.VERY_LOW),
        (20.0, ScoreLevel.LOW),
        (39.99, ScoreLevel.LOW),
        (40.0, ScoreLevel.MEDIUM),
        (59.99, ScoreLevel.MEDIUM),
        (60.0, ScoreLevel.HIGH),
        (79.99, ScoreLevel.HIGH),
        (80.0, ScoreLevel.VERY_HIGH),
        (100.0, ScoreLevel.VERY_HIGH),
    ],
)
def test_score_level_from_score(
    score: float,
    expected_level: ScoreLevel,
) -> None:
    assert ScoreLevel.from_score(score) == expected_level


@pytest.mark.parametrize(
    "score",
    [
        -0.01,
        100.01,
    ],
)
def test_score_level_rejects_out_of_range_score(
    score: float,
) -> None:
    with pytest.raises(
        ValueError,
        match="score must be between",
    ):
        ScoreLevel.from_score(score)
