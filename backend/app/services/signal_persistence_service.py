from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from app.domain.events import SignalEvent
from app.models.signal import Signal
from app.repositories import SignalRepository, ZoneRepository


SignalPayloadFingerprint = Callable[
    [dict[str, Any]],
    tuple[object, ...],
]


@dataclass(frozen=True)
class SignalZoneConfiguration:
    city: str
    country: str
    latitude: float
    longitude: float

    def __post_init__(self) -> None:
        normalized_city = self.city.strip()
        normalized_country = self.country.strip()

        if not normalized_city:
            raise ValueError("city cannot be empty")

        if not normalized_country:
            raise ValueError("country cannot be empty")

        if not -90.0 <= self.latitude <= 90.0:
            raise ValueError("latitude must be between -90 and 90")

        if not -180.0 <= self.longitude <= 180.0:
            raise ValueError("longitude must be between -180 and 180")

        object.__setattr__(
            self,
            "city",
            normalized_city,
        )
        object.__setattr__(
            self,
            "country",
            normalized_country,
        )


class SignalPersistenceService:
    def __init__(
        self,
        *,
        zone_repository: ZoneRepository,
        signal_repository: SignalRepository,
        zone_configuration: SignalZoneConfiguration,
        payload_fingerprint: SignalPayloadFingerprint,
        deduplication_window: timedelta = timedelta(minutes=5),
    ) -> None:
        if deduplication_window <= timedelta(0):
            raise ValueError("deduplication_window must be positive")

        self._zone_repository = zone_repository
        self._signal_repository = signal_repository
        self._zone_configuration = zone_configuration
        self._payload_fingerprint = payload_fingerprint
        self._deduplication_window = deduplication_window

    async def persist(
        self,
        signal: SignalEvent,
    ) -> Signal:
        zone = await self._zone_repository.get_by_name(signal.zone_name)

        if zone is None:
            zone = await self._zone_repository.create(
                name=signal.zone_name,
                city=self._zone_configuration.city,
                country=self._zone_configuration.country,
                latitude=(self._zone_configuration.latitude),
                longitude=(self._zone_configuration.longitude),
            )

        observed_since = signal.observed_at - self._deduplication_window

        existing_signal = await self._signal_repository.get_latest_since(
            signal_type=signal.signal_type.value,
            source=signal.source.value,
            zone_id=zone.id,
            observed_since=observed_since,
        )

        if existing_signal is not None and self._has_same_payload(
            stored_payload=existing_signal.payload,
            current_payload=signal.payload,
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

    def _has_same_payload(
        self,
        *,
        stored_payload: dict[str, Any],
        current_payload: dict[str, Any],
    ) -> bool:
        return self._payload_fingerprint(stored_payload) == self._payload_fingerprint(
            current_payload
        )
