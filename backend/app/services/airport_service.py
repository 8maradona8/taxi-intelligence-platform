from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore
from app.models.signal import Signal
from app.services.signal_service import SignalService
from app.services.zone_service import ZoneService


class AirportService:
    def __init__(self, session: AsyncSession) -> None:
        self.zone_service = ZoneService(session)
        self.signal_service = SignalService(session)

    def create_airport_activity_event(
        self,
        *,
        airport_code: str,
        arrivals: int,
        departures: int,
    ) -> SignalEvent:
        impact_score = float(arrivals * 10 + departures * 3)

        return SignalEvent(
            source=SignalSource.AIRPORT,
            signal_type=SignalType.AIRPORT_ACTIVITY,
            zone_name="Sofia Airport",
            impact_score=ImpactScore(impact_score),
            confidence=Confidence(0.9),
            priority=PriorityLevel.HIGH,
            ttl=timedelta(minutes=45),
            payload={
                "airport": airport_code,
                "arrivals": arrivals,
                "departures": departures,
            },
        )

    async def persist_signal_event(self, signal_event: SignalEvent) -> Signal:
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

    async def create_airport_activity_signal(
        self,
        *,
        airport_code: str,
        arrivals: int,
        departures: int,
    ) -> Signal:
        signal_event = self.create_airport_activity_event(
            airport_code=airport_code,
            arrivals=arrivals,
            departures=departures,
        )

        return await self.persist_signal_event(signal_event)