from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces.scheduler_failure_breakdown import (
    SchedulerFailureBreakdown,
)
from app.application.interfaces.scheduler_reliability_trend import (
    SchedulerReliabilityTrend,
)
from app.application.interfaces.scheduler_run_metrics import (
    SchedulerRunMetrics,
)
from app.application.interfaces.scheduler_runtime import (
    SchedulerRuntimeStatus,
)


@dataclass(frozen=True)
class SchedulerObservabilityOverview:
    observed_at: datetime
    scheduler_status: SchedulerRuntimeStatus | None
    metrics: SchedulerRunMetrics
    failure_breakdown: SchedulerFailureBreakdown
    reliability_trend: SchedulerReliabilityTrend
