from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces import (
    SchedulerReliabilityTrend,
)


@dataclass(frozen=True)
class SchedulerReliabilityTrendPointResponse:
    period_started_at: datetime
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate_percent: float
    average_duration_ms: float
    average_attempts: float
    total_retry_attempts: int


@dataclass(frozen=True)
class SchedulerReliabilityTrendResponse:
    scheduler_name: str
    window: str
    granularity: str
    window_started_at: datetime | None
    window_ended_at: datetime
    point_count: int
    points: list[SchedulerReliabilityTrendPointResponse]

    @classmethod
    def from_trend(
        cls,
        trend: SchedulerReliabilityTrend,
    ) -> "SchedulerReliabilityTrendResponse":
        points = [
            SchedulerReliabilityTrendPointResponse(
                period_started_at=(point.period_started_at),
                total_runs=point.total_runs,
                successful_runs=(point.successful_runs),
                failed_runs=point.failed_runs,
                success_rate_percent=(point.success_rate_percent),
                average_duration_ms=(point.average_duration_ms),
                average_attempts=(point.average_attempts),
                total_retry_attempts=(point.total_retry_attempts),
            )
            for point in trend.points
        ]

        return cls(
            scheduler_name=trend.scheduler_name,
            window=trend.window.value,
            granularity=trend.granularity.value,
            window_started_at=(trend.window_started_at),
            window_ended_at=trend.window_ended_at,
            point_count=trend.point_count,
            points=points,
        )
