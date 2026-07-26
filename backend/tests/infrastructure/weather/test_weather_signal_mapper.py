from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.domain import WeatherForecast
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.infrastructure.mappers.weather.weather_signal_mapper import (
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
    assert signal.signal_type == SignalType.WEATHER_CONDITION
    assert signal.zone_name == "Sofia"
    assert signal.priority == PriorityLevel.LOW
    assert signal.impact_score.value == 0.0
    assert signal.confidence.value == 0.95
    assert signal.observed_at == observed_at
    assert signal.payload["provider"] == "met-norway"
    assert signal.payload["location"] == "Sofia"
    assert signal.payload["arrivals"] == 0
    assert signal.payload["demand_impact_scored"] is False
    assert signal.payload["scoring_version"] == "raw-weather-v1"
    assert signal.payload["forecast_window_minutes"] == 360
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


def test_weather_mapper_uses_inclusive_window_end() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    mapper = WeatherSignalMapper(
        forecast_window=timedelta(hours=6),
    )

    signal = mapper.map_forecasts(
        [
            make_forecast(
                forecast_at=observed_at,
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=6),
            ),
            make_forecast(
                forecast_at=observed_at
                + timedelta(
                    hours=6,
                    seconds=1,
                ),
            ),
        ],
        observed_at=observed_at,
    )

    assert signal.payload["forecast_count"] == 2
    assert (
        signal.payload["forecasts"][1]["forecast_at"]
        == (observed_at + timedelta(hours=6)).isoformat()
    )


def test_weather_mapper_orders_unsorted_forecasts() -> None:
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
            make_forecast(
                forecast_at=observed_at + timedelta(hours=2),
                temperature=26.0,
            ),
            make_forecast(
                forecast_at=observed_at,
                temperature=24.0,
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=1),
                temperature=25.0,
            ),
        ],
        observed_at=observed_at,
    )

    serialized_forecasts = signal.payload["forecasts"]

    assert [
        forecast["air_temperature_celsius"] for forecast in serialized_forecasts
    ] == [
        24.0,
        25.0,
        26.0,
    ]
    assert signal.payload["current"]["air_temperature_celsius"] == 24.0


def test_weather_mapper_selects_first_future_forecast() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        30,
        tzinfo=UTC,
    )

    signal = WeatherSignalMapper().map_forecasts(
        [
            make_forecast(
                forecast_at=datetime(
                    2026,
                    7,
                    21,
                    12,
                    0,
                    tzinfo=UTC,
                ),
                temperature=24.0,
            ),
            make_forecast(
                forecast_at=datetime(
                    2026,
                    7,
                    21,
                    13,
                    0,
                    tzinfo=UTC,
                ),
                temperature=25.0,
            ),
        ],
        observed_at=observed_at,
    )

    assert signal.payload["current"]["air_temperature_celsius"] == 25.0


def test_weather_mapper_uses_last_forecast_when_all_are_past() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        15,
        0,
        tzinfo=UTC,
    )

    signal = WeatherSignalMapper().map_forecasts(
        [
            make_forecast(
                forecast_at=observed_at - timedelta(hours=2),
                temperature=22.0,
            ),
            make_forecast(
                forecast_at=observed_at - timedelta(hours=1),
                temperature=23.0,
            ),
        ],
        observed_at=observed_at,
    )

    assert signal.payload["forecast_count"] == 1
    assert signal.payload["current"]["air_temperature_celsius"] == 23.0
    assert signal.payload["forecasts"][0] == signal.payload["current"]


def test_weather_mapper_normalizes_observed_at_to_utc() -> None:
    sofia_timezone = timezone(timedelta(hours=3))
    observed_at = datetime(
        2026,
        7,
        21,
        15,
        0,
        tzinfo=sofia_timezone,
    )
    forecast_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    signal = WeatherSignalMapper().map_forecasts(
        [
            make_forecast(
                forecast_at=forecast_at,
            )
        ],
        observed_at=observed_at,
    )

    assert signal.observed_at == forecast_at


def test_weather_mapper_normalizes_zone_name() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    signal = WeatherSignalMapper(
        zone_name=" Sofia Airport ",
    ).map_forecasts(
        [
            make_forecast(
                forecast_at=observed_at,
            )
        ],
        observed_at=observed_at,
    )

    assert signal.zone_name == "Sofia Airport"
    assert signal.payload["location"] == "Sofia Airport"


def test_weather_mapper_rejects_empty_forecasts() -> None:
    with pytest.raises(
        ValueError,
        match="forecasts cannot be empty",
    ):
        WeatherSignalMapper().map_forecasts([])


def test_weather_mapper_rejects_duplicate_forecast_times() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    with pytest.raises(
        ValueError,
        match=("forecasts cannot contain duplicate forecast_at values"),
    ):
        WeatherSignalMapper().map_forecasts(
            [
                make_forecast(
                    forecast_at=observed_at,
                    temperature=20.0,
                ),
                make_forecast(
                    forecast_at=observed_at,
                    temperature=21.0,
                ),
            ],
            observed_at=observed_at,
        )


@pytest.mark.parametrize(
    ("arguments", "message"),
    [
        (
            {"zone_name": "   "},
            "zone_name cannot be empty",
        ),
        (
            {"forecast_window": timedelta(0)},
            "forecast_window must be positive",
        ),
        (
            {"forecast_window": timedelta(seconds=-1)},
            "forecast_window must be positive",
        ),
        (
            {"signal_ttl": timedelta(0)},
            "signal_ttl must be positive",
        ),
        (
            {"signal_ttl": timedelta(seconds=-1)},
            "signal_ttl must be positive",
        ),
    ],
)
def test_weather_mapper_rejects_invalid_configuration(
    arguments: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(
        ValueError,
        match=message,
    ):
        WeatherSignalMapper(**arguments)  # type: ignore[arg-type]
