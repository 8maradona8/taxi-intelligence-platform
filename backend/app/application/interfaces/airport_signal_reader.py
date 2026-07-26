from typing import Protocol

from app.domain.events import SignalEvent


class AirportSignalReader(Protocol):
    async def get_latest_active_signal(
        self,
    ) -> SignalEvent | None:
        """Return the latest active airport signal."""
