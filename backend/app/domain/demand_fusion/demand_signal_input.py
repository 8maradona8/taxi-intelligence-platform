from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from math import isfinite
from typing import Any

from app.domain.enums import (
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent


@dataclass(frozen=True, slots=True)
class DemandSignalInput:
    """Normalized signal input consumed by demand fusion."""

    source: SignalSource
    signal_type: SignalType
    zone_name: str
    score: float
    confidence: float
    observed_at: datetime
    expires_at: datetime
    metadata: Mapping[str, Any] = field(
        default_factory=dict,
    )

    def __post_init__(self) -> None:
        normalized_zone_name = self.zone_name.strip()

        if not normalized_zone_name:
            raise ValueError("zone_name cannot be empty")

        if not isfinite(self.score):
            raise ValueError("score must be finite")

        if not 0.0 <= self.score <= 100.0:
            raise ValueError("score must be between 0.0 and 100.0")

        if not isfinite(self.confidence):
            raise ValueError("confidence must be finite")

        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")

        normalized_observed_at = self._normalize_datetime(
            self.observed_at,
            field_name="observed_at",
        )
        normalized_expires_at = self._normalize_datetime(
            self.expires_at,
            field_name="expires_at",
        )

        if normalized_expires_at <= normalized_observed_at:
            raise ValueError("expires_at must be after observed_at")

        object.__setattr__(
            self,
            "zone_name",
            normalized_zone_name,
        )
        object.__setattr__(
            self,
            "observed_at",
            normalized_observed_at,
        )
        object.__setattr__(
            self,
            "expires_at",
            normalized_expires_at,
        )

    @classmethod
    def from_signal_event(
        cls,
        signal: SignalEvent,
    ) -> "DemandSignalInput":
        """Create a fusion input from an existing signal event."""
        return cls(
            source=signal.source,
            signal_type=signal.signal_type,
            zone_name=signal.zone_name,
            score=signal.impact_score.value,
            confidence=signal.confidence.value,
            observed_at=signal.observed_at,
            expires_at=signal.expires_at,
            metadata=dict(signal.payload),
        )

    def is_active_at(
        self,
        moment: datetime,
    ) -> bool:
        normalized_moment = self._normalize_datetime(
            moment,
            field_name="moment",
        )

        return self.observed_at <= normalized_moment < self.expires_at

    @staticmethod
    def _normalize_datetime(
        value: datetime,
        *,
        field_name: str,
    ) -> datetime:
        if value.tzinfo is None:
            raise ValueError(f"{field_name} must be timezone-aware")

        return value.astimezone(UTC)
