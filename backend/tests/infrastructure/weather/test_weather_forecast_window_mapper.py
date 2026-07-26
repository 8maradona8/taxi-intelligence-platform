from datetime import UTC, datetime, timedelta

import pytest

from app.application.scoring.weather import (
    WeatherScoreService,
)
from app.domain.enums import PriorityLevel
from app.domain.weather import WeatherForecast
from app.infrastructure.mappers.weather.weather_signal_mapper import (
    WeatherSignalMapper,
)


def make_forecast(
    *,
    forecast_at: datetime,
    temperature: float = 20.0,
    wind_speed: float = 2.0,
    precipitation: float = 0.0,
    symbol_code: str = "clearsky_day",
) -> WeatherForecast:
    return WeatherForecast(
        forecast_at=forecast_at,
        air_temperature_celsius=temperature,
        relative_humidity_percent=60.0,
        wind_speed_mps=wind_speed,
        wind_from_direction_degrees=180.0,
        cloud_area_fraction_percent=20.0,
        air_pressure_at_sea_level_hpa=1015.0,
        precipitation_amount_mm=precipitation,
        symbol_code=symbol_code,
    )


def test_mapper_uses_peak_forecast_assessment_for_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )
    peak_forecast_at = observed_at + timedelta(hours=2)

    mapper = WeatherSignalMapper(
        forecast_window=timedelta(hours=6),
        score_service=WeatherScoreService(),
    )

    signal = mapper.map_forecasts(
        [
            make_forecast(
                forecast_at=observed_at,
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=1),
                wind_speed=5.0,
            ),
            make_forecast(
                forecast_at=peak_forecast_at,
                temperature=4.0,
                wind_speed=12.0,
                precipitation=2.5,
                symbol_code="heavyrain",
            ),
        ],
        observed_at=observed_at,
    )

    forecast_scoring = signal.payload["forecast_scoring"]

    assert signal.impact_score.value == pytest.approx(
        71.73,
        abs=0.01,
    )
    assert signal.priority == PriorityLevel.HIGH

    assert forecast_scoring["scoring_version"] == ("weather-forecast-window-v1")
    assert forecast_scoring["window_minutes"] == 360
    assert forecast_scoring["forecast_count"] == 3
    assert forecast_scoring["peak_score"] == pytest.approx(
        71.73,
        abs=0.01,
    )
    assert forecast_scoring["peak_forecast_at"] == (peak_forecast_at.isoformat())

    assessments = forecast_scoring["assessments"]

    assert len(assessments) == 3
    assert [assessment["horizon_minutes"] for assessment in assessments] == [0, 60, 120]

    assert signal.payload["scoring"]["score"] == (forecast_scoring["peak_score"])


def test_mapper_excludes_forecasts_outside_configured_window() -> None:
    observed_at = datetime(
        2026,
        7,
        26,
        12,
        0,
        tzinfo=UTC,
    )

    mapper = WeatherSignalMapper(
        forecast_window=timedelta(hours=3),
        score_service=WeatherScoreService(),
    )

    signal = mapper.map_forecasts(
        [
            make_forecast(
                forecast_at=observed_at,
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=2),
                precipitation=1.0,
                symbol_code="rain",
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=8),
                temperature=1.0,
                wind_speed=15.0,
                precipitation=5.0,
                symbol_code="heavyrain",
            ),
        ],
        observed_at=observed_at,
    )

    forecast_scoring = signal.payload["forecast_scoring"]

    assert forecast_scoring["window_minutes"] == 180
    assert forecast_scoring["forecast_count"] == 2
    assert len(forecast_scoring["assessments"]) == 2
