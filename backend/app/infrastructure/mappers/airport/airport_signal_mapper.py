from collections import Counter
from datetime import UTC, datetime, timedelta

from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.flight import Flight
from app.domain.flight_status import FlightStatus
from app.domain.value_objects import Confidence, ImpactScore


class AirportSignalMapper:
    def __init__(
        self,
        *,
        zone_name: str = "Sofia Airport",
        forecast_window: timedelta = timedelta(hours=2),
        signal_ttl: timedelta = timedelta(minutes=15),
    ) -> None:
        if forecast_window <= timedelta(0):
            raise ValueError("forecast_window must be positive")

        if signal_ttl <= timedelta(0):
            raise ValueError("signal_ttl must be positive")

        self._zone_name = zone_name
        self._forecast_window = forecast_window
        self._signal_ttl = signal_ttl

    def map_arrivals(
        self,
        flights: list[Flight],
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        observation_time = observed_at or datetime.now(UTC)

        relevant_flights = self._select_relevant_flights(
            flights,
            observed_at=observation_time,
        )

        scheduled_count = self._count_status(
            relevant_flights,
            FlightStatus.SCHEDULED,
        )
        expected_count = self._count_status(
            relevant_flights,
            FlightStatus.EXPECTED,
        )
        delayed_count = self._count_status(
            relevant_flights,
            FlightStatus.DELAYED,
        )
        cancelled_count = self._count_status(
            relevant_flights,
            FlightStatus.CANCELLED,
        )

        terminal_counts = Counter(
            flight.terminal or "Unknown" for flight in relevant_flights
        )

        impact_score = self._calculate_impact_score(
            relevant_flights=relevant_flights,
            delayed_count=delayed_count,
            cancelled_count=cancelled_count,
        )

        confidence = self._calculate_confidence(relevant_flights)

        priority = self._calculate_priority(impact_score)

        return SignalEvent(
            source=SignalSource.AIRPORT,
            signal_type=SignalType.AIRPORT_ACTIVITY,
            zone_name=self._zone_name,
            impact_score=ImpactScore(impact_score),
            confidence=Confidence(confidence),
            priority=priority,
            observed_at=observation_time,
            ttl=self._signal_ttl,
            payload={
                "airport": "SOF",
                "forecast_window_minutes": int(
                    self._forecast_window.total_seconds() / 60
                ),
                "arrivals": len(relevant_flights),
                "scheduled": scheduled_count,
                "expected": expected_count,
                "delayed": delayed_count,
                "cancelled": cancelled_count,
                "terminal_distribution": dict(terminal_counts),
                "flight_numbers": [flight.flight_number for flight in relevant_flights],
            },
        )

    def _select_relevant_flights(
        self,
        flights: list[Flight],
        *,
        observed_at: datetime,
    ) -> list[Flight]:
        window_end = observed_at + self._forecast_window

        return [
            flight
            for flight in flights
            if not flight.is_cancelled
            and observed_at <= flight.effective_arrival <= window_end
        ]

    @staticmethod
    def _count_status(
        flights: list[Flight],
        status: FlightStatus,
    ) -> int:
        return sum(flight.status == status for flight in flights)

    @staticmethod
    def _calculate_impact_score(
        *,
        relevant_flights: list[Flight],
        delayed_count: int,
        cancelled_count: int,
    ) -> float:
        base_score = len(relevant_flights) * 12.0
        delayed_bonus = delayed_count * 8.0
        cancellation_penalty = cancelled_count * 5.0

        score = base_score + delayed_bonus - cancellation_penalty

        return min(
            100.0,
            max(0.0, score),
        )

    @staticmethod
    def _calculate_confidence(
        relevant_flights: list[Flight],
    ) -> float:
        if not relevant_flights:
            return 0.50

        known_status_count = sum(
            flight.status != FlightStatus.UNKNOWN for flight in relevant_flights
        )

        status_coverage = known_status_count / len(relevant_flights)

        return round(
            min(
                0.98,
                0.70 + status_coverage * 0.25,
            ),
            2,
        )

    @staticmethod
    def _calculate_priority(
        impact_score: float,
    ) -> PriorityLevel:
        if impact_score >= 80:
            return PriorityLevel.HIGH

        if impact_score >= 40:
            return PriorityLevel.MEDIUM

        return PriorityLevel.LOW
