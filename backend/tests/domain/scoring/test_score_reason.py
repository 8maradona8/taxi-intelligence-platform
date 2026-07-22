import pytest

from app.domain.scoring import ScoreReason


def test_score_reason_normalizes_text() -> None:
    reason = ScoreReason(
        code="  moderate_rain  ",
        description="  Moderate rain increases demand  ",
        contribution=22.0,
    )

    assert reason.code == "moderate_rain"
    assert reason.description == ("Moderate rain increases demand")
    assert reason.contribution == 22.0


@pytest.mark.parametrize(
    ("field_name", "field_value", "error"),
    [
        ("code", "   ", "code cannot be empty"),
        (
            "description",
            "   ",
            "description cannot be empty",
        ),
    ],
)
def test_score_reason_rejects_empty_text(
    field_name: str,
    field_value: str,
    error: str,
) -> None:
    values = {
        "code": "rain",
        "description": "Rain",
    }
    values[field_name] = field_value

    with pytest.raises(ValueError, match=error):
        ScoreReason(**values)


@pytest.mark.parametrize(
    "contribution",
    [
        -100.01,
        100.01,
        float("inf"),
    ],
)
def test_score_reason_rejects_invalid_contribution(
    contribution: float,
) -> None:
    with pytest.raises(ValueError):
        ScoreReason(
            code="rain",
            description="Rain",
            contribution=contribution,
        )
