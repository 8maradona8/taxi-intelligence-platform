from datetime import UTC, datetime
from typing import Any

import pytest

from app.domain import WeatherForecast
from app.infrastructure.collectors import (
    SofiaWeatherCollector,
)


class FakeWeatherClient:
    def __init__(self) -> None:
        self.received_latitude: float | None = None
        self.received_longitude: float | None = None
        self.received_altitude: int | None = None
        self.payload: dict[str, Any] = {
            "weather": "payload",
        }

    async def get_location_forecast(
        self,
        *,
        latitude: float,
        longitude: float,
        altitude: int | None = None,
    ) -> dict[str, Any]:
        self.received_latitude = latitude
        self.received_longitude = longitude
        self.received_altitude = altitude

        return self.payload


class FakeWeatherParser:
    def __init__(self) -> None:
        self.received_payload: dict[str, Any] | None = None
        self.forecasts = [
            WeatherForecast(
                forecast_at=datetime(
                    2026,
                    7,
                    21,
                    12,
                    0,
                    tzinfo=UTC,
                ),
                air_temperature_celsius=29.7,
                relative_humidity_percent=32.8,
                wind_speed_mps=3.3,
                wind_from_direction_degrees=330.9,
                cloud_area_fraction_percent=4.7,
                air_pressure_at_sea_level_hpa=1015.7,
                precipitation_amount_mm=0.0,
                symbol_code="clearsky_day",
            )
        ]

    def parse_forecasts(
        self,
        payload: dict[str, Any],
    ) -> list[WeatherForecast]:
        self.received_payload = payload

        return self.forecasts


@pytest.mark.anyio
async def test_collector_returns_parsed_forecasts() -> None:
    client = FakeWeatherClient()
    parser = FakeWeatherParser()

    collector = SofiaWeatherCollector(
        client=client,  # type: ignore[arg-type]
        parser=parser,  # type: ignore[arg-type]
    )

    forecasts = await collector.collect_forecasts()

    assert client.received_latitude == 42.6977
    assert client.received_longitude == 23.3219
    assert client.received_altitude == 550
    assert parser.received_payload == client.payload
    assert forecasts == parser.forecasts


@pytest.mark.anyio
async def test_collector_uses_custom_coordinates() -> None:
    client = FakeWeatherClient()
    parser = FakeWeatherParser()

    collector = SofiaWeatherCollector(
        client=client,  # type: ignore[arg-type]
        parser=parser,  # type: ignore[arg-type]
        latitude=42.65,
        longitude=23.40,
        altitude=600,
    )

    await collector.collect_forecasts()

    assert client.received_latitude == 42.65
    assert client.received_longitude == 23.40
    assert client.received_altitude == 600


@pytest.mark.parametrize(
    ("latitude", "longitude", "altitude"),
    [
        (-91.0, 23.3219, 550),
        (91.0, 23.3219, 550),
        (42.6977, -181.0, 550),
        (42.6977, 181.0, 550),
        (42.6977, 23.3219, -501),
        (42.6977, 23.3219, 9001),
    ],
)
def test_collector_rejects_invalid_location(
    latitude: float,
    longitude: float,
    altitude: int,
) -> None:
    with pytest.raises(ValueError):
        SofiaWeatherCollector(
            client=FakeWeatherClient(),  # type: ignore[arg-type]
            parser=FakeWeatherParser(),  # type: ignore[arg-type]
            latitude=latitude,
            longitude=longitude,
            altitude=altitude,
        )
