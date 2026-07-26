from datetime import datetime

import pytest

from app.application.scoring import ScoreContributor
from app.application.scoring.weather import (
    WindScoreContributor,
)
from tests.application.scoring.weather.conftest import (
    make_weather_context,
)


def test_wind_contributor_satisfies_protocol() -> None:
    assert isinstance(
        WindScoreContributor(),
        ScoreContributor,
    )


@pytest.mark.parametrize(
    (
        "wind_speed_mps",
        "expected_score",
        "expected_code",
    ),
    [
        (
            0.0,
            10.0,
            "weather_calm_wind",
        ),
        (
            2.9999,
            10.0,
            "weather_calm_wind",
        ),
        (
            3.0,
            25.0,
            "weather_light_wind",
        ),
        (
            5.9999,
            25.0,
            "weather_light_wind",
        ),
        (
            6.0,
            50.0,
            "weather_strong_wind",
        ),
        (
            9.9999,
            50.0,
            "weather_strong_wind",
        ),
        (
            10.0,
            75.0,
            "weather_very_strong_wind",
        ),
        (
            14.9999,
            75.0,
            "weather_very_strong_wind",
        ),
        (
            15.0,
            90.0,
            "weather_extreme_wind",
        ),
    ],
)
def test_wind_thresholds(
    observed_at: datetime,
    wind_speed_mps: float,
    expected_score: float,
    expected_code: str,
) -> None:
    context = make_weather_context(
        observed_at=observed_at,
        wind_speed_mps=wind_speed_mps,
    )

    contribution = WindScoreContributor().evaluate(context)

    assert contribution.contributor == "weather_wind"
    assert contribution.score == expected_score
    assert contribution.reason.code == expected_code


def test_wind_contribution_contains_metadata(
    observed_at: datetime,
) -> None:
    contribution = WindScoreContributor().evaluate(
        make_weather_context(
            observed_at=observed_at,
            wind_speed_mps=12.0,
        )
    )

    assert contribution.weight == 0.20
    assert contribution.confidence == 0.90
    assert contribution.metadata["wind_speed_mps"] == 12.0
    assert contribution.reason.metadata["wind_from_direction_degrees"] == 180.0
