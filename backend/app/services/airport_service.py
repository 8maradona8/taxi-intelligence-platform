from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.engines import SignalEngine
from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore
from app.models.signal import Signal


class AirportService:
    def __init__(self, session: AsyncSession) -> None:
        self.signal_engine = SignalEngine(session)

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

        return await self.signal_engine.persist(signal_event)
