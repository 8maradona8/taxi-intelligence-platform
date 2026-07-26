from datetime import UTC, datetime

import pytest

from app.application.scoring.weather import (
    WeatherScoreService,
)
from app.domain.scoring import ScoreLevel
from app.domain.weather import (
    WeatherForecast,
    WeatherSnapshot,
)


def make_snapshot() -> WeatherSnapshot:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    return WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            WeatherForecast(
                forecast_at=observed_at,
                air_temperature_celsius=4.0,
                relative_humidity_percent=85.0,
                wind_speed_mps=12.0,
                wind_from_direction_degrees=180.0,
                cloud_area_fraction_percent=90.0,
                air_pressure_at_sea_level_hpa=1002.0,
                precipitation_amount_mm=2.5,
                symbol_code="heavyrain",
            )
        ],
    )


def test_weather_score_service_assesses_snapshot() -> None:
    assessment = WeatherScoreService().assess_snapshot(
        make_snapshot(),
    )

    assert assessment.score == pytest.approx(
        71.73,
        abs=0.01,
    )
    assert assessment.confidence == pytest.approx(
        0.925,
    )
    assert assessment.level == ScoreLevel.HIGH
    assert len(assessment.contributions) == 3
    assert {contribution.contributor for contribution in assessment.contributions} == {
        "weather_precipitation",
        "weather_temperature",
        "weather_wind",
    }


def test_weather_score_service_exposes_aggregation_metadata() -> None:
    assessment = WeatherScoreService().assess_snapshot(
        make_snapshot(),
    )

    assert assessment.metadata["aggregation_method"] == (
        "confidence_adjusted_weighted_average"
    )
    assert assessment.metadata["contributors_count"] == 3
    assert assessment.metadata["total_weight"] == 1.0
    assert assessment.metadata["effective_weight"] == pytest.approx(
        0.925,
    )
