from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.events import SignalEvent
from app.infrastructure.collectors import (
    SofiaCentralBusStationCollector,
)
from app.infrastructure.mappers import BusSignalMapper
from app.services.bus_signal_persistence_service import (
    BusSignalPersistenceService,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class BusSignalService:
    def __init__(
        self,
        *,
        collector: SofiaCentralBusStationCollector,
        signal_mapper: BusSignalMapper,
        persistence_service: BusSignalPersistenceService | None = None,
    ) -> None:
        self._collector = collector
        self._signal_mapper = signal_mapper
        self._persistence_service = persistence_service

    async def create_arrivals_signal(
        self,
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        observation_time = self._normalize_observed_at(
            observed_at,
        )

        arrivals = await self._collector.collect_arrivals(
            observed_at=observation_time,
        )

        signal = self._signal_mapper.map_arrivals(
            arrivals,
            observed_at=observation_time,
        )

        if self._persistence_service is not None:
            await self._persistence_service.persist(signal)

        return signal

    @staticmethod
    def _normalize_observed_at(
        observed_at: datetime | None,
    ) -> datetime:
        if observed_at is None:
            return datetime.now(SOFIA_TIMEZONE)

        if observed_at.tzinfo is None:
            return observed_at.replace(
                tzinfo=SOFIA_TIMEZONE,
            )

        return observed_at.astimezone(
            SOFIA_TIMEZONE,
        )
