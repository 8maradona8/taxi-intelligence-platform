from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces.scheduler_metrics_window import (
    SchedulerMetricsWindow,
)


@dataclass(frozen=True)
class SchedulerFailureGroup:
    error_type: str
    count: int
    last_occurred_at: datetime
    latest_message: str | None


@dataclass(frozen=True)
class SchedulerFailureBreakdown:
    scheduler_name: str
    window: SchedulerMetricsWindow
    window_started_at: datetime | None
    window_ended_at: datetime
    total_failures: int
    failures: list[SchedulerFailureGroup]

    @property
    def distinct_error_types(self) -> int:
        return len(self.failures)

    def share_percent(
        self,
        *,
        count: int,
    ) -> float:
        if self.total_failures == 0:
            return 0.0

        return round(
            count / self.total_failures * 100,
            2,
        )
