from datetime import UTC, datetime

from app.application.scoring.weather import (
    WeatherScoreService,
)
from app.domain.enums import PriorityLevel
from app.domain.weather import WeatherForecast
from app.infrastructure.mappers.weather import (
    WeatherSignalMapper,
)


def make_extreme_weather_forecast(
    *,
    forecast_at: datetime,
) -> WeatherForecast:
    return WeatherForecast(
        forecast_at=forecast_at,
        air_temperature_celsius=-15.0,
        relative_humidity_percent=95.0,
        wind_speed_mps=16.0,
        wind_from_direction_degrees=180.0,
        cloud_area_fraction_percent=100.0,
        air_pressure_at_sea_level_hpa=990.0,
        precipitation_amount_mm=8.0,
        symbol_code="heavyrainandthunder",
    )


def test_weather_mapper_creates_scored_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    signal = WeatherSignalMapper(
        score_service=WeatherScoreService(),
    ).map_forecasts(
        [
            make_extreme_weather_forecast(
                forecast_at=observed_at,
            )
        ],
        observed_at=observed_at,
    )

    assert signal.impact_score.value > 90.0
    assert signal.confidence.value == 0.925
    assert signal.priority == PriorityLevel.CRITICAL

    assert signal.payload["demand_impact_scored"] is True
    assert signal.payload["scoring_version"] == ("weather-demand-v1")

    scoring = signal.payload["scoring"]

    assert scoring["score"] == signal.impact_score.value
    assert scoring["confidence"] == signal.confidence.value
    assert scoring["level"] == "very_high"
    assert len(scoring["contributors"]) == 3
    assert len(scoring["reasons"]) == 3


def test_weather_mapper_scoring_uses_current_forecast() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    comfortable_forecast = WeatherForecast(
        forecast_at=observed_at,
        air_temperature_celsius=22.0,
        relative_humidity_percent=55.0,
        wind_speed_mps=1.0,
        wind_from_direction_degrees=180.0,
        cloud_area_fraction_percent=10.0,
        air_pressure_at_sea_level_hpa=1015.0,
        precipitation_amount_mm=0.0,
        symbol_code="clearsky_day",
    )

    signal = WeatherSignalMapper(
        score_service=WeatherScoreService(),
    ).map_forecasts(
        [comfortable_forecast],
        observed_at=observed_at,
    )

    assert signal.impact_score.value == 10.0
    assert signal.priority == PriorityLevel.LOW
    assert signal.payload["scoring"]["level"] == "very_low"


def test_weather_mapper_preserves_raw_mode_without_score_service() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    signal = WeatherSignalMapper().map_forecasts(
        [
            make_extreme_weather_forecast(
                forecast_at=observed_at,
            )
        ],
        observed_at=observed_at,
    )

    assert signal.impact_score.value == 0.0
    assert signal.confidence.value == 0.95
    assert signal.priority == PriorityLevel.LOW
    assert signal.payload["demand_impact_scored"] is False
    assert signal.payload["scoring_version"] == "raw-weather-v1"
    assert "scoring" not in signal.payload
