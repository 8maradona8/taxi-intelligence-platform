from datetime import datetime
from typing import Protocol


class SchedulerRuntimeStatus(Protocol):
    name: str
    running: bool
    interval_seconds: float
    run_on_startup: bool
    started_at: datetime | None
    next_run_at: datetime | None
    last_started_at: datetime | None
    last_completed_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None
    last_impact_score: float | None
    last_arrivals: int | None
    runs_total: int
    successes_total: int
    failures_total: int
    recovering: bool
    max_attempts: int
    current_attempt: int | None
    retry_backoff_seconds: float
    retry_attempts_total: int
    overlap_skips_total: int


class SchedulerRuntime(Protocol):
    @property
    def status(
        self,
    ) -> SchedulerRuntimeStatus: ...
