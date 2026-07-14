from dataclasses import dataclass
from datetime import datetime

from app.models.scheduler_run import SchedulerRun


@dataclass(frozen=True)
class SchedulerRunHistoryItemResponse:
    id: int
    status: str
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    attempts: int
    retry_attempts: int
    impact_score: float | None
    arrivals: int | None
    error_type: str | None
    error_message: str | None

    @classmethod
    def from_model(
        cls,
        run: SchedulerRun,
    ) -> "SchedulerRunHistoryItemResponse":
        return cls(
            id=run.id,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_ms=run.duration_ms,
            attempts=run.attempts,
            retry_attempts=run.retry_attempts,
            impact_score=run.impact_score,
            arrivals=run.arrivals,
            error_type=run.error_type,
            error_message=run.error_message,
        )


@dataclass(frozen=True)
class SchedulerRunHistoryResponse:
    scheduler_name: str
    count: int
    runs: list[SchedulerRunHistoryItemResponse]

    @classmethod
    def from_models(
        cls,
        *,
        scheduler_name: str,
        runs: list[SchedulerRun],
    ) -> "SchedulerRunHistoryResponse":
        items = [SchedulerRunHistoryItemResponse.from_model(run) for run in runs]

        return cls(
            scheduler_name=scheduler_name,
            count=len(items),
            runs=items,
        )
