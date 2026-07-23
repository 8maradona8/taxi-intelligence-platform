from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone

import pytest

from app.domain.weather import (
    WeatherForecast,
    WeatherSnapshot,
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


def test_weather_snapshot_normalizes_metadata() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    snapshot = WeatherSnapshot.create(
        location=" Sofia ",
        provider=" MET-Norway ",
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at,
            )
        ],
    )

    assert snapshot.location == "Sofia"
    assert snapshot.provider == "met-norway"


def test_weather_snapshot_normalizes_naive_observed_at_to_utc() -> None:
    naive_observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=naive_observed_at,
        forecasts=[
            make_forecast(
                forecast_at=naive_observed_at.replace(tzinfo=UTC),
            )
        ],
    )

    assert snapshot.observed_at == naive_observed_at.replace(tzinfo=UTC)


def test_weather_snapshot_converts_observed_at_to_utc() -> None:
    sofia_timezone = timezone(timedelta(hours=3))
    observed_at = datetime(
        2026,
        7,
        21,
        15,
        0,
        tzinfo=sofia_timezone,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=datetime(
                    2026,
                    7,
                    21,
                    12,
                    0,
                    tzinfo=UTC,
                )
            )
        ],
    )

    assert snapshot.observed_at == datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )


def test_weather_snapshot_orders_forecasts_chronologically() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )
    first = make_forecast(
        forecast_at=observed_at,
        temperature=20.0,
    )
    second = make_forecast(
        forecast_at=observed_at + timedelta(hours=1),
        temperature=21.0,
    )
    third = make_forecast(
        forecast_at=observed_at + timedelta(hours=2),
        temperature=22.0,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            third,
            first,
            second,
        ],
    )

    assert snapshot.forecasts == (
        first,
        second,
        third,
    )


def test_weather_snapshot_stores_immutable_forecast_tuple() -> None:
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
        )
    ]

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=forecasts,
    )

    forecasts.append(
        make_forecast(
            forecast_at=observed_at + timedelta(hours=1),
        )
    )

    assert isinstance(snapshot.forecasts, tuple)
    assert snapshot.forecast_count == 1

    with pytest.raises(FrozenInstanceError):
        snapshot.location = "Plovdiv"  # type: ignore[misc]


def test_weather_snapshot_selects_forecast_at_observation_time() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )
    current = make_forecast(
        forecast_at=observed_at,
        temperature=24.0,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at - timedelta(hours=1),
                temperature=23.0,
            ),
            current,
            make_forecast(
                forecast_at=observed_at + timedelta(hours=1),
                temperature=25.0,
            ),
        ],
    )

    assert snapshot.current_forecast is current


def test_weather_snapshot_selects_first_future_forecast() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        30,
        tzinfo=UTC,
    )
    expected = make_forecast(
        forecast_at=datetime(
            2026,
            7,
            21,
            13,
            0,
            tzinfo=UTC,
        ),
        temperature=25.0,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
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
            expected,
        ],
    )

    assert snapshot.current_forecast is expected


def test_weather_snapshot_selects_last_forecast_when_all_are_past() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        15,
        0,
        tzinfo=UTC,
    )
    expected = make_forecast(
        forecast_at=observed_at - timedelta(hours=1),
        temperature=24.0,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at - timedelta(hours=2),
                temperature=23.0,
            ),
            expected,
        ],
    )

    assert snapshot.current_forecast is expected


def test_weather_snapshot_filters_inclusive_forecast_window() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )
    at_start = make_forecast(
        forecast_at=observed_at,
    )
    inside = make_forecast(
        forecast_at=observed_at + timedelta(hours=3),
    )
    at_end = make_forecast(
        forecast_at=observed_at + timedelta(hours=6),
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at - timedelta(hours=1),
            ),
            at_start,
            inside,
            at_end,
            make_forecast(
                forecast_at=observed_at + timedelta(hours=7),
            ),
        ],
    )

    result = snapshot.forecasts_within(timedelta(hours=6))

    assert result == (
        at_start,
        inside,
        at_end,
    )


def test_weather_snapshot_returns_empty_window_when_no_forecasts_match() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at - timedelta(hours=1),
            ),
            make_forecast(
                forecast_at=observed_at + timedelta(hours=8),
            ),
        ],
    )

    assert snapshot.forecasts_within(timedelta(hours=6)) == ()


@pytest.mark.parametrize(
    "window",
    [
        timedelta(0),
        timedelta(seconds=-1),
    ],
)
def test_weather_snapshot_rejects_non_positive_window(
    window: timedelta,
) -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    snapshot = WeatherSnapshot.create(
        observed_at=observed_at,
        forecasts=[
            make_forecast(
                forecast_at=observed_at,
            )
        ],
    )

    with pytest.raises(
        ValueError,
        match="window must be positive",
    ):
        snapshot.forecasts_within(window)


def test_weather_snapshot_rejects_empty_forecasts() -> None:
    with pytest.raises(
        ValueError,
        match="forecasts cannot be empty",
    ):
        WeatherSnapshot.create(
            observed_at=datetime(
                2026,
                7,
                21,
                12,
                0,
                tzinfo=UTC,
            ),
            forecasts=[],
        )


def test_weather_snapshot_rejects_duplicate_forecast_times() -> None:
    forecast_at = datetime(
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
        WeatherSnapshot.create(
            observed_at=forecast_at,
            forecasts=[
                make_forecast(
                    forecast_at=forecast_at,
                    temperature=20.0,
                ),
                make_forecast(
                    forecast_at=forecast_at,
                    temperature=21.0,
                ),
            ],
        )


@pytest.mark.parametrize(
    ("field_name", "value", "message"),
    [
        (
            "location",
            "   ",
            "location cannot be empty",
        ),
        (
            "provider",
            "   ",
            "provider cannot be empty",
        ),
    ],
)
def test_weather_snapshot_rejects_empty_metadata(
    field_name: str,
    value: str,
    message: str,
) -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )
    arguments: dict[str, object] = {
        "location": "Sofia",
        "provider": "met-norway",
        "observed_at": observed_at,
        "forecasts": [
            make_forecast(
                forecast_at=observed_at,
            )
        ],
    }
    arguments[field_name] = value

    with pytest.raises(
        ValueError,
        match=message,
    ):
        WeatherSnapshot(
            location=arguments["location"],  # type: ignore[arg-type]
            provider=arguments["provider"],  # type: ignore[arg-type]
            observed_at=arguments["observed_at"],  # type: ignore[arg-type]
            forecasts=tuple(
                arguments["forecasts"]  # type: ignore[arg-type]
            ),
        )
