from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal
from app.services.signal_service import SignalService
from app.services.zone_service import ZoneService


class AirportService:
    def __init__(self, session: AsyncSession) -> None:
        self.zone_service = ZoneService(session)
        self.signal_service = SignalService(session)

    async def create_airport_activity_signal(
        self,
        *,
        airport_code: str,
        arrivals: int,
        departures: int,
    ) -> Signal:
        zone = await self.zone_service.get_or_create_zone(
            name="Sofia Airport",
            city="Sofia",
            country="Bulgaria",
            latitude=42.6967,
            longitude=23.4114,
        )

        impact_score = float(arrivals * 10 + departures * 3)

        return await self.signal_service.create_signal(
            signal_type="airport_activity",
            source="airport_service",
            zone_id=zone.id,
            impact_score=impact_score,
            observed_at=datetime.now(UTC),
            payload={
                "airport": airport_code,
                "arrivals": arrivals,
                "departures": departures,
            },
        )