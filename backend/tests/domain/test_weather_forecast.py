from dataclasses import FrozenInstanceError
from datetime import UTC, datetime

import pytest

from app.domain import (
    PrecipitationType,
    WeatherCondition,
    WeatherForecast,
)


def make_forecast(
    **overrides: object,
) -> WeatherForecast:
    values: dict[str, object] = {
        "forecast_at": datetime(
            2026,
            7,
            21,
            12,
            0,
            tzinfo=UTC,
        ),
        "air_temperature_celsius": 29.7,
        "relative_humidity_percent": 32.8,
        "wind_speed_mps": 3.3,
        "wind_from_direction_degrees": 330.9,
        "cloud_area_fraction_percent": 4.7,
        "air_pressure_at_sea_level_hpa": 1015.7,
        "precipitation_amount_mm": 0.0,
        "symbol_code": " ClearSky_Day ",
    }

    values.update(overrides)

    return WeatherForecast(
        forecast_at=values["forecast_at"],  # type: ignore[arg-type]
        air_temperature_celsius=values["air_temperature_celsius"],  # type: ignore[arg-type]
        relative_humidity_percent=values["relative_humidity_percent"],  # type: ignore[arg-type]
        wind_speed_mps=values["wind_speed_mps"],  # type: ignore[arg-type]
        wind_from_direction_degrees=values["wind_from_direction_degrees"],  # type: ignore[arg-type]
        cloud_area_fraction_percent=values["cloud_area_fraction_percent"],  # type: ignore[arg-type]
        air_pressure_at_sea_level_hpa=values["air_pressure_at_sea_level_hpa"],  # type: ignore[arg-type]
        precipitation_amount_mm=values["precipitation_amount_mm"],  # type: ignore[arg-type]
        symbol_code=values["symbol_code"],  # type: ignore[arg-type]
    )


def test_weather_forecast_normalizes_symbol_code() -> None:
    forecast = make_forecast()

    assert forecast.symbol_code == "clearsky_day"


def test_weather_forecast_is_immutable() -> None:
    forecast = make_forecast()

    with pytest.raises(FrozenInstanceError):
        forecast.symbol_code = "rain"  # type: ignore[misc]


def test_weather_forecast_exposes_condition() -> None:
    forecast = make_forecast(
        symbol_code="rainshowers_day",
        precipitation_amount_mm=1.5,
    )

    assert forecast.condition == WeatherCondition.RAIN


def test_weather_forecast_exposes_precipitation_type() -> None:
    forecast = make_forecast(
        symbol_code="snow",
        precipitation_amount_mm=2.0,
    )

    assert forecast.precipitation_type == PrecipitationType.SNOW


def test_weather_forecast_detects_precipitation() -> None:
    dry_forecast = make_forecast()
    wet_forecast = make_forecast(
        symbol_code="rain",
        precipitation_amount_mm=0.1,
    )

    assert dry_forecast.has_precipitation is False
    assert wet_forecast.has_precipitation is True


def test_weather_forecast_rejects_naive_datetime() -> None:
    with pytest.raises(
        ValueError,
        match="forecast_at must be timezone-aware",
    ):
        make_forecast(
            forecast_at=datetime(
                2026,
                7,
                21,
                12,
                0,
            )
        )


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("air_temperature_celsius", -101.0),
        ("air_temperature_celsius", 71.0),
        ("relative_humidity_percent", -1.0),
        ("relative_humidity_percent", 101.0),
        ("wind_speed_mps", -0.1),
        ("wind_from_direction_degrees", -1.0),
        ("wind_from_direction_degrees", 361.0),
        ("cloud_area_fraction_percent", -1.0),
        ("cloud_area_fraction_percent", 101.0),
        ("air_pressure_at_sea_level_hpa", 0.0),
        ("precipitation_amount_mm", -0.1),
        ("symbol_code", "   "),
    ],
)
def test_weather_forecast_rejects_invalid_values(
    field_name: str,
    value: object,
) -> None:
    with pytest.raises(ValueError):
        make_forecast(
            **{
                field_name: value,
            }
        )


def test_legacy_weather_forecast_import_is_compatible() -> None:
    from app.domain.weather_forecast import (  # noqa: PLC0415
        WeatherForecast as LegacyWeatherForecast,
    )

    assert LegacyWeatherForecast is WeatherForecast
