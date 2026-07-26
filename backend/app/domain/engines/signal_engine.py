from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.events import SignalEvent
from app.models.signal import Signal
from app.services.signal_service import SignalService
from app.services.zone_service import ZoneService


class SignalEngine:
    def __init__(self, session: AsyncSession) -> None:
        self.zone_service = ZoneService(session)
        self.signal_service = SignalService(session)

    async def persist(self, signal_event: SignalEvent) -> Signal:
        zone = await self.zone_service.get_or_create_zone(
            name=signal_event.zone_name,
            city="Sofia",
            country="Bulgaria",
            latitude=42.6967,
            longitude=23.4114,
        )

        return await self.signal_service.create_signal(
            signal_type=signal_event.signal_type.value,
            source=signal_event.source.value,
            zone_id=zone.id,
            impact_score=signal_event.impact_score.value,
            observed_at=signal_event.observed_at,
            payload={
                **signal_event.payload,
                "confidence": signal_event.confidence.value,
                "priority": signal_event.priority.value,
                "expires_at": signal_event.expires_at.isoformat(),
            },
        )
