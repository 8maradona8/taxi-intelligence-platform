from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any

from app.domain.enums.priority_level import PriorityLevel
from app.domain.enums.signal_source import SignalSource
from app.domain.enums.signal_type import SignalType
from app.domain.value_objects.confidence import Confidence
from app.domain.value_objects.impact_score import ImpactScore


@dataclass(frozen=True)
class SignalEvent:
    source: SignalSource
    signal_type: SignalType
    zone_name: str
    impact_score: ImpactScore
    confidence: Confidence
    priority: PriorityLevel
    observed_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    ttl: timedelta = field(default=timedelta(minutes=60))
    payload: dict[str, Any] = field(default_factory=dict)

    @property
    def expires_at(self) -> datetime:
        return self.observed_at + self.ttl

    @property
    def is_expired(self) -> bool:
        return datetime.now(UTC) >= self.expires_at