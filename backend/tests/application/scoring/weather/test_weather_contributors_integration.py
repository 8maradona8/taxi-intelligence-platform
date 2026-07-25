from datetime import datetime

import pytest

from app.application.scoring import (
    ScoreEngineBuilder,
)
from app.application.scoring.weather import (
    PrecipitationScoreContributor,
    TemperatureScoreContributor,
    WindScoreContributor,
)
from tests.application.scoring.weather.conftest import (
    make_weather_context,
)


def test_weather_contributors_integrate_with_score_engine(
    observed_at: datetime,
) -> None:
    engine = (
        ScoreEngineBuilder()
        .add_many(
            (
                PrecipitationScoreContributor(),
                WindScoreContributor(),
                TemperatureScoreContributor(),
            )
        )
        .build()
    )

    context = make_weather_context(
        observed_at=observed_at,
        precipitation_amount_mm=3.0,
        symbol_code="heavyrain",
        wind_speed_mps=12.0,
        temperature_celsius=35.0,
    )

    assessment = engine.assess(context)

    expected_score = (
        (80.0 * 0.50 * 0.95) + (75.0 * 0.20 * 0.90) + (70.0 * 0.30 * 0.90)
    ) / ((0.50 * 0.95) + (0.20 * 0.90) + (0.30 * 0.90))

    assert assessment.score == pytest.approx(
        round(expected_score, 2),
    )
    assert assessment.confidence == pytest.approx(0.925)
    assert tuple(
        contribution.contributor for contribution in assessment.contributions
    ) == (
        "weather_precipitation",
        "weather_wind",
        "weather_temperature",
    )
    assert tuple(reason.code for reason in assessment.reasons) == (
        "weather_heavy_precipitation",
        "weather_very_strong_wind",
        "weather_very_hot",
    )
