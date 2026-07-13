from datetime import datetime
from zoneinfo import ZoneInfo

from app.domain.events import SignalEvent
from app.infrastructure.collectors import SofiaAirportCollector
from app.infrastructure.mappers import AirportSignalMapper


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class AirportSignalService:
    def __init__(
        self,
        *,
        collector: SofiaAirportCollector,
        signal_mapper: AirportSignalMapper,
    ) -> None:
        self._collector = collector
        self._signal_mapper = signal_mapper

    async def create_arrivals_signal(self) -> SignalEvent:
        flights = await self._collector.collect_arrivals()

        return self._signal_mapper.map_arrivals(
            flights,
            observed_at=datetime.now(SOFIA_TIMEZONE),
        )