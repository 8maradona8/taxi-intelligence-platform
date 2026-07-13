from datetime import datetime
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal


class SignalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_latest_since(
        self,
        *,
        signal_type: str,
        source: str,
        zone_id: int,
        observed_since: datetime,
    ) -> Signal | None:
        result = await self.session.execute(
            select(Signal)
            .where(
                Signal.signal_type == signal_type,
                Signal.source == source,
                Signal.zone_id == zone_id,
                Signal.observed_at >= observed_since,
            )
            .order_by(Signal.observed_at.desc())
            .limit(1)
        )

        return result.scalar_one_or_none()

    async def create(
        self,
        *,
        signal_type: str,
        source: str,
        zone_id: int,
        impact_score: float,
        observed_at: datetime,
        payload: dict[str, Any],
    ) -> Signal:
        signal = Signal(
            signal_type=signal_type,
            source=source,
            zone_id=zone_id,
            impact_score=impact_score,
            observed_at=observed_at,
            payload=payload,
        )

        self.session.add(signal)
        await self.session.commit()
        await self.session.refresh(signal)

        return signal
