from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore
from app.models.signal import Signal
from app.repositories import SignalRepository, ZoneRepository


class AirportSignalReadService:
    def __init__(
        self,
        *,
        zone_repository: ZoneRepository,
        signal_repository: SignalRepository,
        candidate_limit: int = 20,
    ) -> None:
        if candidate_limit <= 0:
            raise ValueError("candidate_limit must be greater than zero")

        self._zone_repository = zone_repository
        self._signal_repository = signal_repository
        self._candidate_limit = candidate_limit

    async def get_latest_active_signal(
        self,
        *,
        now: datetime | None = None,
    ) -> SignalEvent | None:
        zone = await self._zone_repository.get_by_name("Sofia Airport")

        if zone is None:
            return None

        stored_signals = await self._signal_repository.list_latest(
            signal_type=SignalType.AIRPORT_ACTIVITY.value,
            source=SignalSource.AIRPORT.value,
            zone_id=zone.id,
            limit=self._candidate_limit,
        )

        current_time = now or datetime.now(UTC)

        for stored_signal in stored_signals:
            signal = self._to_domain(
                stored_signal,
                zone_name=zone.name,
            )

            if current_time < signal.expires_at:
                return signal

        return None

    @staticmethod
    def _to_domain(
        stored_signal: Signal,
        *,
        zone_name: str,
    ) -> SignalEvent:
        payload: dict[str, Any] = dict(stored_signal.payload or {})

        confidence = AirportSignalReadService._safe_confidence(
            payload.get("confidence")
        )

        priority = AirportSignalReadService._safe_priority(payload.get("priority"))

        ttl_seconds = AirportSignalReadService._safe_ttl_seconds(
            payload.get("ttl_seconds")
        )

        observed_at = stored_signal.observed_at

        if observed_at.tzinfo is None:
            observed_at = observed_at.replace(tzinfo=UTC)

        domain_payload = {
            key: value
            for key, value in payload.items()
            if key
            not in {
                "confidence",
                "priority",
                "ttl_seconds",
            }
        }

        return SignalEvent(
            source=SignalSource.AIRPORT,
            signal_type=SignalType.AIRPORT_ACTIVITY,
            zone_name=zone_name,
            impact_score=ImpactScore(stored_signal.impact_score),
            confidence=Confidence(confidence),
            priority=priority,
            observed_at=observed_at,
            ttl=timedelta(seconds=ttl_seconds),
            payload=domain_payload,
        )

    @staticmethod
    def _safe_confidence(value: object) -> float:
        try:
            confidence = float(value)
        except (TypeError, ValueError):
            return 0.50

        return min(1.0, max(0.0, confidence))

    @staticmethod
    def _safe_priority(value: object) -> PriorityLevel:
        try:
            return PriorityLevel(str(value))
        except ValueError:
            return PriorityLevel.LOW

    @staticmethod
    def _safe_ttl_seconds(value: object) -> int:
        try:
            ttl_seconds = int(value)
        except (TypeError, ValueError):
            return 900

        return max(1, ttl_seconds)
