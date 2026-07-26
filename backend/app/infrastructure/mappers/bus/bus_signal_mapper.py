from collections import Counter
from datetime import UTC, datetime, timedelta

from app.domain import BusArrival
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import (
    Confidence,
    ImpactScore,
)


class BusSignalMapper:
    def __init__(
        self,
        *,
        zone_name: str = "Sofia Central Bus Station",
        station_code: str = "sofia-central-bus-station",
        forecast_window: timedelta = timedelta(hours=2),
        signal_ttl: timedelta = timedelta(minutes=15),
    ) -> None:
        if forecast_window <= timedelta(0):
            raise ValueError("forecast_window must be positive")

        if signal_ttl <= timedelta(0):
            raise ValueError("signal_ttl must be positive")

        normalized_zone_name = zone_name.strip()
        normalized_station_code = station_code.strip().lower()

        if not normalized_zone_name:
            raise ValueError("zone_name cannot be empty")

        if not normalized_station_code:
            raise ValueError("station_code cannot be empty")

        self._zone_name = normalized_zone_name
        self._station_code = normalized_station_code
        self._forecast_window = forecast_window
        self._signal_ttl = signal_ttl

    def map_arrivals(
        self,
        arrivals: list[BusArrival],
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        observation_time = observed_at or datetime.now(UTC)

        relevant_arrivals = self._select_relevant_arrivals(
            arrivals,
            observed_at=observation_time,
        )

        origins = sorted({arrival.origin for arrival in relevant_arrivals})

        carriers = sorted({arrival.carrier for arrival in relevant_arrivals})

        carrier_distribution = Counter(arrival.carrier for arrival in relevant_arrivals)

        sector_distribution = Counter(
            arrival.sector or "Unknown" for arrival in relevant_arrivals
        )

        known_sector_count = sum(
            arrival.sector is not None for arrival in relevant_arrivals
        )

        impact_score = self._calculate_impact_score(
            arrivals_count=len(relevant_arrivals),
            unique_origins_count=len(origins),
            known_sector_count=known_sector_count,
        )

        confidence = self._calculate_confidence(relevant_arrivals)

        priority = self._calculate_priority(impact_score)

        return SignalEvent(
            source=SignalSource.TRANSPORT,
            signal_type=SignalType.TRANSPORT_ACTIVITY,
            zone_name=self._zone_name,
            impact_score=ImpactScore(impact_score),
            confidence=Confidence(confidence),
            priority=priority,
            observed_at=observation_time,
            ttl=self._signal_ttl,
            payload={
                "mode": "bus",
                "station": self._zone_name,
                "station_code": self._station_code,
                "forecast_window_minutes": int(
                    self._forecast_window.total_seconds() / 60
                ),
                "arrivals": len(relevant_arrivals),
                "unique_origins": len(origins),
                "known_sectors": known_sector_count,
                "origins": origins,
                "carriers": carriers,
                "carrier_distribution": dict(carrier_distribution),
                "sector_distribution": dict(sector_distribution),
                "arrival_times": [
                    arrival.scheduled_arrival.isoformat()
                    for arrival in relevant_arrivals
                ],
                "routes": [arrival.route for arrival in relevant_arrivals],
            },
        )

    def _select_relevant_arrivals(
        self,
        arrivals: list[BusArrival],
        *,
        observed_at: datetime,
    ) -> list[BusArrival]:
        window_end = observed_at + self._forecast_window

        return [
            arrival
            for arrival in arrivals
            if (observed_at <= arrival.scheduled_arrival <= window_end)
        ]

    @staticmethod
    def _calculate_impact_score(
        *,
        arrivals_count: int,
        unique_origins_count: int,
        known_sector_count: int,
    ) -> float:
        base_score = arrivals_count * 10.0

        origin_bonus = min(
            15.0,
            unique_origins_count * 3.0,
        )

        sector_bonus = known_sector_count * 2.0

        score = base_score + origin_bonus + sector_bonus

        return min(
            100.0,
            max(
                0.0,
                score,
            ),
        )

    @staticmethod
    def _calculate_confidence(
        arrivals: list[BusArrival],
    ) -> float:
        if not arrivals:
            return 0.50

        total = len(arrivals)

        carrier_coverage = sum(bool(arrival.carrier) for arrival in arrivals) / total

        route_coverage = (
            sum(bool(arrival.route and arrival.full_route) for arrival in arrivals)
            / total
        )

        sector_coverage = (
            sum(arrival.sector is not None for arrival in arrivals) / total
        )

        confidence = (
            0.72
            + carrier_coverage * 0.13
            + route_coverage * 0.08
            + sector_coverage * 0.05
        )

        return round(
            min(
                0.98,
                confidence,
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
