from datetime import UTC, datetime, timedelta

import pytest

from app.domain import WeatherForecast
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.infrastructure.mappers import (
    WeatherSignalMapper,
)


def make_forecast(
    *,
    forecast_at: datetime,
    temperature: float = 18.0,
    precipitation: float = 0.0,
    symbol_code: str = "partlycloudy_day",
) -> WeatherForecast:
    return WeatherForecast(
        forecast_at=forecast_at,
        air_temperature_celsius=temperature,
        relative_humidity_percent=65.0,
        wind_speed_mps=3.5,
        wind_from_direction_degrees=180.0,
        cloud_area_fraction_percent=45.0,
        air_pressure_at_sea_level_hpa=1014.0,
        precipitation_amount_mm=precipitation,
        symbol_code=symbol_code,
    )


def test_weather_mapper_creates_raw_weather_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    forecasts = [
        make_forecast(
            forecast_at=observed_at,
            temperature=24.0,
        ),
        make_forecast(
            forecast_at=observed_at + timedelta(hours=1),
            precipitation=1.5,
            symbol_code="rain",
        ),
    ]

    signal = WeatherSignalMapper().map_forecasts(
        forecasts,
        observed_at=observed_at,
    )

    assert signal.source == SignalSource.WEATHER
    assert signal.signal_type == (SignalType.WEATHER_CONDITION)
    assert signal.zone_name == "Sofia"
    assert signal.priority == PriorityLevel.LOW
    assert signal.impact_score.value == 0.0
    assert signal.confidence.value == 0.95
    assert signal.payload["arrivals"] == 0
    assert signal.payload["demand_impact_scored"] is False
    assert signal.payload["forecast_count"] == 2
    assert signal.payload["current"]["air_temperature_celsius"] == 24.0


def test_weather_mapper_filters_forecast_window() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    forecasts = [
        make_forecast(
            forecast_at=observed_at,
        ),
        make_forecast(
            forecast_at=observed_at + timedelta(hours=2),
        ),
        make_forecast(
            forecast_at=observed_at + timedelta(hours=8),
        ),
    ]

    mapper = WeatherSignalMapper(
        forecast_window=timedelta(hours=6),
    )

    signal = mapper.map_forecasts(
        forecasts,
        observed_at=observed_at,
    )

    assert signal.payload["forecast_count"] == 2


def test_weather_mapper_rejects_empty_forecasts() -> None:
    with pytest.raises(
        ValueError,
        match="forecasts cannot be empty",
    ):
        WeatherSignalMapper().map_forecasts([])
