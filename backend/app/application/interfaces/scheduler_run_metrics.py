from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class SchedulerRunMetrics:
    scheduler_name: str
    total_runs: int
    successful_runs: int
    failed_runs: int
    average_duration_ms: float
    average_attempts: float
    total_retry_attempts: int
    last_run_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None

    @property
    def success_rate_percent(self) -> float:
        if self.total_runs == 0:
            return 0.0

        return round(
            self.successful_runs / self.total_runs * 100,
            2,
        )
