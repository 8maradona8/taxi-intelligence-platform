from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal


class SignalRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

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