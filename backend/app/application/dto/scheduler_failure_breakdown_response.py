from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces import (
    SchedulerFailureBreakdown,
)


@dataclass(frozen=True)
class SchedulerFailureItemResponse:
    error_type: str
    count: int
    share_percent: float
    last_occurred_at: datetime
    latest_message: str | None


@dataclass(frozen=True)
class SchedulerFailureBreakdownResponse:
    scheduler_name: str
    window: str
    window_started_at: datetime | None
    window_ended_at: datetime
    total_failures: int
    distinct_error_types: int
    failures: list[SchedulerFailureItemResponse]

    @classmethod
    def from_breakdown(
        cls,
        breakdown: SchedulerFailureBreakdown,
    ) -> "SchedulerFailureBreakdownResponse":
        items = [
            SchedulerFailureItemResponse(
                error_type=failure.error_type,
                count=failure.count,
                share_percent=breakdown.share_percent(count=failure.count),
                last_occurred_at=(failure.last_occurred_at),
                latest_message=(failure.latest_message),
            )
            for failure in breakdown.failures
        ]

        return cls(
            scheduler_name=breakdown.scheduler_name,
            window=breakdown.window.value,
            window_started_at=(breakdown.window_started_at),
            window_ended_at=breakdown.window_ended_at,
            total_failures=breakdown.total_failures,
            distinct_error_types=(breakdown.distinct_error_types),
            failures=items,
        )
