from datetime import UTC, datetime

from app.domain.events import SignalEvent
from app.infrastructure.collectors import (
    SofiaWeatherCollector,
)
from app.infrastructure.mappers import (
    WeatherSignalMapper,
)
from app.services.weather_signal_persistence_service import (
    WeatherSignalPersistenceService,
)


class WeatherSignalService:
    def __init__(
        self,
        *,
        collector: SofiaWeatherCollector,
        signal_mapper: WeatherSignalMapper,
        persistence_service: (WeatherSignalPersistenceService | None) = None,
    ) -> None:
        self._collector = collector
        self._signal_mapper = signal_mapper
        self._persistence_service = persistence_service

    async def create_weather_signal(
        self,
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        observation_time = self._normalize_observed_at(observed_at or datetime.now(UTC))

        forecasts = await self._collector.collect_forecasts()

        signal = self._signal_mapper.map_forecasts(
            forecasts,
            observed_at=observation_time,
        )

        if self._persistence_service is not None:
            await self._persistence_service.persist(signal)

        return signal

    @staticmethod
    def _normalize_observed_at(
        observed_at: datetime,
    ) -> datetime:
        if observed_at.tzinfo is None:
            return observed_at.replace(tzinfo=UTC)

        return observed_at.astimezone(UTC)
