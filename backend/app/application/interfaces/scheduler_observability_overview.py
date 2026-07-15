from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from app.application.interfaces.scheduler_failure_breakdown import (
    SchedulerFailureBreakdown,
)
from app.application.interfaces.scheduler_reliability_trend import (
    SchedulerReliabilityTrend,
)
from app.application.interfaces.scheduler_run_metrics import (
    SchedulerRunMetrics,
)

if TYPE_CHECKING:
    from app.schedulers.airport_scheduler import (
        AirportSchedulerStatus,
    )


@dataclass(frozen=True)
class SchedulerObservabilityOverview:
    observed_at: datetime
    scheduler_status: "AirportSchedulerStatus | None"
    metrics: SchedulerRunMetrics
    failure_breakdown: SchedulerFailureBreakdown
    reliability_trend: SchedulerReliabilityTrend
