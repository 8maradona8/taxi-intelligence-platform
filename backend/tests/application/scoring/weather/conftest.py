from datetime import UTC, datetime

import pytest

from app.domain.scoring import ScoreContext
from app.domain.weather import (
    WeatherForecast,
    WeatherSnapshot,
)


@pytest.fixture
def observed_at() -> datetime:
    return datetime(
        2026,
        7,
        24,
        12,
        0,
        tzinfo=UTC,
    )


def make_weather_context(
    *,
    observed_at: datetime,
    precipitation_amount_mm: float = 0.0,
    symbol_code: str = "clearsky_day",
    wind_speed_mps: float = 2.0,
    temperature_celsius: float = 20.0,
) -> ScoreContext:
    forecast = WeatherForecast(
        forecast_at=observed_at,
        air_temperature_celsius=temperature_celsius,
        relative_humidity_percent=60.0,
        wind_speed_mps=wind_speed_mps,
        wind_from_direction_degrees=180.0,
        cloud_area_fraction_percent=20.0,
        air_pressure_at_sea_level_hpa=1015.0,
        precipitation_amount_mm=precipitation_amount_mm,
        symbol_code=symbol_code,
    )

    snapshot = WeatherSnapshot.create(
        location="Sofia",
        provider="met-norway",
        observed_at=observed_at,
        forecasts=(forecast,),
    )

    return ScoreContext(
        subject="weather",
        observed_at=observed_at,
        attributes={
            "weather_snapshot": snapshot,
        },
    )
