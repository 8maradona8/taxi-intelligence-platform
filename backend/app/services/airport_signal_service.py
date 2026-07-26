from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.events import SignalEvent
from app.infrastructure.collectors import SofiaAirportCollector
from app.infrastructure.mappers import AirportSignalMapper
from app.services.airport_signal_persistence_service import (
    AirportSignalPersistenceService,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class AirportSignalService:
    def __init__(
        self,
        *,
        collector: SofiaAirportCollector,
        signal_mapper: AirportSignalMapper,
        persistence_service: (AirportSignalPersistenceService | None) = None,
    ) -> None:
        self._collector = collector
        self._signal_mapper = signal_mapper
        self._persistence_service = persistence_service

    async def create_arrivals_signal(self) -> SignalEvent:
        flights = await self._collector.collect_arrivals()

        signal = self._signal_mapper.map_arrivals(
            flights,
            observed_at=datetime.now(SOFIA_TIMEZONE),
        )

        if self._persistence_service is not None:
            await self._persistence_service.persist(signal)

        return signal
