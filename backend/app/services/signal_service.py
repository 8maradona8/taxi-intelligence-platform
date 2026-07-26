from datetime import datetime
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.signal import Signal
from app.repositories.signal_repository import SignalRepository


class SignalService:
    def __init__(self, session: AsyncSession) -> None:
        self.signal_repository = SignalRepository(session)

    async def create_signal(
        self,
        *,
        signal_type: str,
        source: str,
        zone_id: int,
        impact_score: float,
        observed_at: datetime,
        payload: dict[str, Any],
    ) -> Signal:
        return await self.signal_repository.create(
            signal_type=signal_type,
            source=source,
            zone_id=zone_id,
            impact_score=impact_score,
            observed_at=observed_at,
            payload=payload,
        )
