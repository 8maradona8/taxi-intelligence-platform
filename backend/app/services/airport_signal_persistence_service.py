from datetime import timedelta
from typing import Any

from app.domain.events import SignalEvent
from app.models.signal import Signal
from app.repositories import SignalRepository, ZoneRepository


class AirportSignalPersistenceService:
    SOFIA_AIRPORT_LATITUDE = 42.6967
    SOFIA_AIRPORT_LONGITUDE = 23.4114

    def __init__(
        self,
        *,
        zone_repository: ZoneRepository,
        signal_repository: SignalRepository,
        deduplication_window: timedelta = timedelta(minutes=5),
    ) -> None:
        if deduplication_window <= timedelta(0):
            raise ValueError("deduplication_window must be positive")

        self._zone_repository = zone_repository
        self._signal_repository = signal_repository
        self._deduplication_window = deduplication_window

    async def persist(
        self,
        signal: SignalEvent,
    ) -> Signal:
        zone = await self._zone_repository.get_by_name(signal.zone_name)

        if zone is None:
            zone = await self._zone_repository.create(
                name=signal.zone_name,
                city="Sofia",
                country="Bulgaria",
                latitude=self.SOFIA_AIRPORT_LATITUDE,
                longitude=self.SOFIA_AIRPORT_LONGITUDE,
            )

        observed_since = signal.observed_at - self._deduplication_window

        existing_signal = await self._signal_repository.get_latest_since(
            signal_type=signal.signal_type.value,
            source=signal.source.value,
            zone_id=zone.id,
            observed_since=observed_since,
        )

        if existing_signal is not None and self._has_same_payload(
            existing_signal.payload,
            signal.payload,
        ):
            return existing_signal

        payload = {
            **signal.payload,
            "confidence": signal.confidence.value,
            "priority": signal.priority.value,
            "ttl_seconds": int(signal.ttl.total_seconds()),
        }

        return await self._signal_repository.create(
            signal_type=signal.signal_type.value,
            source=signal.source.value,
            zone_id=zone.id,
            impact_score=signal.impact_score.value,
            observed_at=signal.observed_at,
            payload=payload,
        )

    @staticmethod
    def _has_same_payload(
        stored_payload: dict[str, Any],
        current_payload: dict[str, Any],
    ) -> bool:
        return (
            stored_payload.get("flight_numbers")
            == current_payload.get("flight_numbers")
            and stored_payload.get("arrivals") == current_payload.get("arrivals")
            and stored_payload.get("delayed") == current_payload.get("delayed")
            and stored_payload.get("expected") == current_payload.get("expected")
        )
