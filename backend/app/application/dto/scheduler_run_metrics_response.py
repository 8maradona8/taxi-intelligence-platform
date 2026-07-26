from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces import SchedulerRunMetrics


@dataclass(frozen=True)
class SchedulerRunMetricsResponse:
    scheduler_name: str
    window: str
    window_started_at: datetime | None
    window_ended_at: datetime
    total_runs: int
    successful_runs: int
    failed_runs: int
    success_rate_percent: float
    average_duration_ms: float
    average_attempts: float
    total_retry_attempts: int
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None

    @classmethod
    def from_metrics(
        cls,
        metrics: SchedulerRunMetrics,
    ) -> "SchedulerRunMetricsResponse":
        return cls(
            scheduler_name=metrics.scheduler_name,
            window=metrics.window.value,
            window_started_at=(metrics.window_started_at),
            window_ended_at=metrics.window_ended_at,
            total_runs=metrics.total_runs,
            successful_runs=metrics.successful_runs,
            failed_runs=metrics.failed_runs,
            success_rate_percent=(metrics.success_rate_percent),
            average_duration_ms=(metrics.average_duration_ms),
            average_attempts=(metrics.average_attempts),
            total_retry_attempts=(metrics.total_retry_attempts),
            last_run_at=metrics.last_run_at,
            last_success_at=metrics.last_success_at,
            last_failure_at=metrics.last_failure_at,
        )
