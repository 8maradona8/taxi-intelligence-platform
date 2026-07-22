from datetime import UTC, datetime

import pytest

from app.domain import WeatherForecast
from app.domain.events import SignalEvent
from app.infrastructure.mappers import (
    WeatherSignalMapper,
)
from app.services.weather_signal_service import (
    WeatherSignalService,
)


class FakeWeatherCollector:
    async def collect_forecasts(
        self,
    ) -> list[WeatherForecast]:
        return [
            WeatherForecast(
                forecast_at=datetime(
                    2026,
                    7,
                    21,
                    12,
                    0,
                    tzinfo=UTC,
                ),
                air_temperature_celsius=24.0,
                relative_humidity_percent=58.0,
                wind_speed_mps=3.0,
                wind_from_direction_degrees=180.0,
                cloud_area_fraction_percent=30.0,
                air_pressure_at_sea_level_hpa=1014.0,
                precipitation_amount_mm=0.0,
                symbol_code="fair_day",
            )
        ]


class FakePersistenceService:
    def __init__(self) -> None:
        self.persisted_signal: SignalEvent | None = None

    async def persist(
        self,
        signal: SignalEvent,
    ) -> object:
        self.persisted_signal = signal

        return object()


@pytest.mark.anyio
async def test_weather_service_creates_and_persists_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )

    persistence_service = FakePersistenceService()

    service = WeatherSignalService(
        collector=(
            FakeWeatherCollector()  # type: ignore[arg-type]
        ),
        signal_mapper=WeatherSignalMapper(),
        persistence_service=(
            persistence_service  # type: ignore[arg-type]
        ),
    )

    signal = await service.create_weather_signal(
        observed_at=observed_at,
    )

    assert signal.zone_name == "Sofia"
    assert signal.payload["provider"] == "met-norway"
    assert signal.payload["forecast_count"] == 1
    assert persistence_service.persisted_signal is signal


@pytest.mark.anyio
async def test_weather_service_supports_no_persistence() -> None:
    service = WeatherSignalService(
        collector=(
            FakeWeatherCollector()  # type: ignore[arg-type]
        ),
        signal_mapper=WeatherSignalMapper(),
    )

    signal = await service.create_weather_signal(
        observed_at=datetime(
            2026,
            7,
            21,
            12,
            0,
            tzinfo=UTC,
        )
    )

    assert signal.payload["provider"] == "met-norway"
