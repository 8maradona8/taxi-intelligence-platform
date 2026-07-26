from datetime import datetime

import pytest

from app.application.scoring import ScoreContributor
from app.application.scoring.weather import (
    TemperatureScoreContributor,
)
from tests.application.scoring.weather.conftest import (
    make_weather_context,
)


def test_temperature_contributor_satisfies_protocol() -> None:
    assert isinstance(
        TemperatureScoreContributor(),
        ScoreContributor,
    )


@pytest.mark.parametrize(
    (
        "temperature_celsius",
        "expected_score",
        "expected_code",
    ),
    [
        (
            -10.0001,
            90.0,
            "weather_extreme_cold",
        ),
        (
            -10.0,
            75.0,
            "weather_severe_cold",
        ),
        (
            -0.0001,
            75.0,
            "weather_severe_cold",
        ),
        (
            0.0,
            55.0,
            "weather_cold",
        ),
        (
            4.9999,
            55.0,
            "weather_cold",
        ),
        (
            5.0,
            10.0,
            "weather_comfortable_temperature",
        ),
        (
            28.0,
            10.0,
            "weather_comfortable_temperature",
        ),
        (
            28.0001,
            45.0,
            "weather_hot",
        ),
        (
            33.0,
            45.0,
            "weather_hot",
        ),
        (
            33.0001,
            70.0,
            "weather_very_hot",
        ),
        (
            38.0,
            70.0,
            "weather_very_hot",
        ),
        (
            38.0001,
            90.0,
            "weather_extreme_heat",
        ),
    ],
)
def test_temperature_thresholds(
    observed_at: datetime,
    temperature_celsius: float,
    expected_score: float,
    expected_code: str,
) -> None:
    context = make_weather_context(
        observed_at=observed_at,
        temperature_celsius=temperature_celsius,
    )

    contribution = TemperatureScoreContributor().evaluate(
        context,
    )

    assert contribution.contributor == "weather_temperature"
    assert contribution.score == expected_score
    assert contribution.reason.code == expected_code


def test_temperature_contribution_contains_metadata(
    observed_at: datetime,
) -> None:
    contribution = TemperatureScoreContributor().evaluate(
        make_weather_context(
            observed_at=observed_at,
            temperature_celsius=35.0,
        )
    )

    assert contribution.weight == 0.30
    assert contribution.confidence == 0.90
    assert contribution.metadata["air_temperature_celsius"] == 35.0
