from dataclasses import dataclass
from datetime import datetime

from app.application.dto.scheduler_failure_breakdown_response import (
    SchedulerFailureBreakdownResponse,
)
from app.application.dto.scheduler_reliability_trend_response import (
    SchedulerReliabilityTrendResponse,
)
from app.application.dto.scheduler_run_metrics_response import (
    SchedulerRunMetricsResponse,
)
from app.application.dto.scheduler_status_response import (
    SchedulerStatusResponse,
)
from app.application.interfaces import (
    SchedulerObservabilityOverview,
)


@dataclass(frozen=True)
class SchedulerObservabilityOverviewResponse:
    observed_at: datetime
    scheduler: SchedulerStatusResponse
    reliability: SchedulerRunMetricsResponse
    failures: SchedulerFailureBreakdownResponse
    trend: SchedulerReliabilityTrendResponse

    @classmethod
    def from_overview(
        cls,
        overview: SchedulerObservabilityOverview,
        *,
        scheduler_enabled: bool,
        interval_seconds: float,
        run_on_startup: bool,
        max_attempts: int,
        retry_backoff_seconds: float,
    ) -> "SchedulerObservabilityOverviewResponse":
        if overview.scheduler_status is None:
            scheduler_response = SchedulerStatusResponse.unavailable(
                enabled=scheduler_enabled,
                interval_seconds=interval_seconds,
                run_on_startup=run_on_startup,
                max_attempts=max_attempts,
                retry_backoff_seconds=(retry_backoff_seconds),
            )
        else:
            scheduler_response = SchedulerStatusResponse.from_status(
                overview.scheduler_status
            )

        return cls(
            observed_at=overview.observed_at,
            scheduler=scheduler_response,
            reliability=(SchedulerRunMetricsResponse.from_metrics(overview.metrics)),
            failures=(
                SchedulerFailureBreakdownResponse.from_breakdown(
                    overview.failure_breakdown
                )
            ),
            trend=(
                SchedulerReliabilityTrendResponse.from_trend(overview.reliability_trend)
            ),
        )
