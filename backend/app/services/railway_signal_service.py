from datetime import date, datetime
from zoneinfo import ZoneInfo

from app.domain.events import SignalEvent
from app.infrastructure.collectors import (
    SofiaRailwayCollector,
)
from app.infrastructure.mappers import (
    RailwaySignalMapper,
)
from app.services.railway_signal_persistence_service import (
    RailwaySignalPersistenceService,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class RailwaySignalService:
    def __init__(
        self,
        *,
        collector: SofiaRailwayCollector,
        signal_mapper: RailwaySignalMapper,
        persistence_service: (RailwaySignalPersistenceService | None) = None,
    ) -> None:
        self._collector = collector
        self._signal_mapper = signal_mapper
        self._persistence_service = persistence_service

    async def create_arrivals_signal(
        self,
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        observation_time = observed_at or datetime.now(SOFIA_TIMEZONE)

        service_date = self._service_date(observation_time)

        arrivals = await self._collector.collect_arrivals(
            service_date=service_date,
        )

        signal = self._signal_mapper.map_arrivals(
            arrivals,
            observed_at=observation_time,
        )

        if self._persistence_service is not None:
            await self._persistence_service.persist(signal)

        return signal

    @staticmethod
    def _service_date(
        observed_at: datetime,
    ) -> date:
        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=SOFIA_TIMEZONE)
        else:
            observed_at = observed_at.astimezone(SOFIA_TIMEZONE)

        return observed_at.date()
