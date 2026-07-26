from dataclasses import dataclass
from datetime import datetime
from typing import Any

from app.models.signal import Signal


@dataclass(frozen=True)
class AirportSignalHistoryItemResponse:
    id: int
    airport: str
    impact_score: float
    confidence: float | None
    priority: str | None
    arrivals: int
    scheduled: int
    expected: int
    delayed: int
    cancelled: int
    flight_numbers: list[str]
    terminal_distribution: dict[str, int]
    observed_at: datetime
    created_at: datetime

    @classmethod
    def from_model(
        cls,
        signal: Signal,
    ) -> "AirportSignalHistoryItemResponse":
        payload: dict[str, Any] = signal.payload

        return cls(
            id=signal.id,
            airport=str(payload.get("airport", "SOF")),
            impact_score=signal.impact_score,
            confidence=payload.get("confidence"),
            priority=payload.get("priority"),
            arrivals=int(payload.get("arrivals", 0)),
            scheduled=int(payload.get("scheduled", 0)),
            expected=int(payload.get("expected", 0)),
            delayed=int(payload.get("delayed", 0)),
            cancelled=int(payload.get("cancelled", 0)),
            flight_numbers=list(payload.get("flight_numbers", [])),
            terminal_distribution=dict(payload.get("terminal_distribution", {})),
            observed_at=signal.observed_at,
            created_at=signal.created_at,
        )


@dataclass(frozen=True)
class AirportSignalHistoryResponse:
    airport: str
    count: int
    signals: list[AirportSignalHistoryItemResponse]

    @classmethod
    def from_models(
        cls,
        signals: list[Signal],
    ) -> "AirportSignalHistoryResponse":
        items = [
            AirportSignalHistoryItemResponse.from_model(signal) for signal in signals
        ]

        return cls(
            airport="SOF",
            count=len(items),
            signals=items,
        )
