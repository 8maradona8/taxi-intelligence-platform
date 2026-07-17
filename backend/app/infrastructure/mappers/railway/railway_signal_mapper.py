from collections import Counter
from datetime import UTC, datetime, timedelta

from app.domain import TrainArrival, TrainStatus
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore


class RailwaySignalMapper:
    EXPRESS_TRAIN_CODES = {
        "БВ",
        "МБВ",
        "МБВЗ",
    }

    def __init__(
        self,
        *,
        zone_name: str = "Sofia Central Railway Station",
        station_code: str = "sofia-central",
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
        arrivals: list[TrainArrival],
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        observation_time = observed_at or datetime.now(UTC)

        relevant_arrivals = self._select_relevant_arrivals(
            arrivals,
            observed_at=observation_time,
        )

        scheduled_count = self._count_status(
            relevant_arrivals,
            TrainStatus.SCHEDULED,
        )
        expected_count = self._count_status(
            relevant_arrivals,
            TrainStatus.EXPECTED,
        )
        delayed_count = self._count_status(
            relevant_arrivals,
            TrainStatus.DELAYED,
        )
        early_count = self._count_status(
            relevant_arrivals,
            TrainStatus.EARLY,
        )

        total_positive_delay_minutes = sum(
            max(0, arrival.delay_minutes) for arrival in relevant_arrivals
        )

        train_type_distribution = Counter(
            arrival.train_type_code for arrival in relevant_arrivals
        )

        platform_distribution = Counter(
            arrival.platform
            for arrival in relevant_arrivals
            if arrival.platform is not None
        )

        impact_score = self._calculate_impact_score(
            relevant_arrivals=relevant_arrivals,
            total_positive_delay_minutes=(total_positive_delay_minutes),
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
                "mode": "railway",
                "station": self._zone_name,
                "station_code": self._station_code,
                "forecast_window_minutes": int(
                    self._forecast_window.total_seconds() / 60
                ),
                "arrivals": len(relevant_arrivals),
                "scheduled": scheduled_count,
                "expected": expected_count,
                "delayed": delayed_count,
                "early": early_count,
                "total_positive_delay_minutes": (total_positive_delay_minutes),
                "train_type_distribution": dict(train_type_distribution),
                "platform_distribution": dict(platform_distribution),
                "train_numbers": [
                    arrival.train_number for arrival in relevant_arrivals
                ],
            },
        )

    def _select_relevant_arrivals(
        self,
        arrivals: list[TrainArrival],
        *,
        observed_at: datetime,
    ) -> list[TrainArrival]:
        window_end = observed_at + self._forecast_window

        return [
            arrival
            for arrival in arrivals
            if not arrival.is_cancelled
            and (observed_at <= arrival.effective_arrival <= window_end)
        ]

    @staticmethod
    def _count_status(
        arrivals: list[TrainArrival],
        status: TrainStatus,
    ) -> int:
        return sum(arrival.status == status for arrival in arrivals)

    def _calculate_impact_score(
        self,
        *,
        relevant_arrivals: list[TrainArrival],
        total_positive_delay_minutes: int,
    ) -> float:
        base_score = len(relevant_arrivals) * 10.0

        express_bonus = sum(
            6.0
            for arrival in relevant_arrivals
            if arrival.train_type_code in self.EXPRESS_TRAIN_CODES
        )

        delay_bonus = min(
            20.0,
            total_positive_delay_minutes * 0.5,
        )

        score = base_score + express_bonus + delay_bonus

        return min(
            100.0,
            max(0.0, score),
        )

    @staticmethod
    def _calculate_confidence(
        relevant_arrivals: list[TrainArrival],
    ) -> float:
        if not relevant_arrivals:
            return 0.50

        complete_count = sum(
            bool(
                arrival.train_number
                and arrival.origin_station
                and arrival.train_type_code
            )
            for arrival in relevant_arrivals
        )

        completeness = complete_count / len(relevant_arrivals)

        return round(
            min(
                0.98,
                0.70 + completeness * 0.25,
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
