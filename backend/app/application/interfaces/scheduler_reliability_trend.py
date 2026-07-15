from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces.scheduler_metrics_window import (
    SchedulerMetricsWindow,
)
from app.application.interfaces.scheduler_trend_granularity import (
    SchedulerTrendGranularity,
)


@dataclass(frozen=True)
class SchedulerReliabilityTrendPoint:
    period_started_at: datetime
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_duration_ms: float
    average_attempts: float
    total_retry_attempts: int

    @property
    def success_rate_percent(self) -> float:
        if self.total_runs == 0:
            return 0.0

        return round(
            self.successful_runs / self.total_runs * 100,
            2,
        )


@dataclass(frozen=True)
class SchedulerReliabilityTrend:
    scheduler_name: str
    window: SchedulerMetricsWindow
    granularity: SchedulerTrendGranularity
    window_started_at: datetime | None
    window_ended_at: datetime
    points: list[SchedulerReliabilityTrendPoint]

    @property
    def point_count(self) -> int:
        return len(self.points)
