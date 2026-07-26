from collections.abc import AsyncIterator

from app.database.session import AsyncSessionLocal
from app.repositories import SignalRepository, ZoneRepository
from app.services.airport_signal_history_service import (
    AirportSignalHistoryService,
)


async def get_airport_signal_history_service() -> AsyncIterator[
    AirportSignalHistoryService
]:
    async with AsyncSessionLocal() as session:
        yield AirportSignalHistoryService(
            zone_repository=ZoneRepository(session),
            signal_repository=SignalRepository(session),
        )
