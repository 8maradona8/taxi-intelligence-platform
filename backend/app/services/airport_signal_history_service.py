from app.models.signal import Signal
from app.repositories import SignalRepository, ZoneRepository


class AirportSignalHistoryService:
    def __init__(
        self,
        *,
        zone_repository: ZoneRepository,
        signal_repository: SignalRepository,
    ) -> None:
        self._zone_repository = zone_repository
        self._signal_repository = signal_repository

    async def get_history(
        self,
        *,
        limit: int = 20,
    ) -> list[Signal]:
        zone = await self._zone_repository.get_by_name("Sofia Airport")

        if zone is None:
            return []

        return await self._signal_repository.list_latest(
            signal_type="airport_activity",
            source="airport",
            zone_id=zone.id,
            limit=limit,
        )
