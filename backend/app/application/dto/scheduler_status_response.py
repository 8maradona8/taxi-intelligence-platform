from dataclasses import dataclass
from datetime import datetime

from app.application.interfaces import (
    SchedulerRuntimeStatus,
)


@dataclass(frozen=True)
class SchedulerStatusResponse:
    name: str
    enabled: bool
    initialized: bool
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

    @classmethod
    def from_status(
        cls,
        status: SchedulerRuntimeStatus,
    ) -> "SchedulerStatusResponse":
        return cls(
            name=status.name,
            enabled=True,
            initialized=True,
            running=status.running,
            interval_seconds=status.interval_seconds,
            run_on_startup=status.run_on_startup,
            started_at=status.started_at,
            next_run_at=status.next_run_at,
            last_started_at=status.last_started_at,
            last_completed_at=status.last_completed_at,
            last_success_at=status.last_success_at,
            last_failure_at=status.last_failure_at,
            last_error=status.last_error,
            last_impact_score=status.last_impact_score,
            last_arrivals=status.last_arrivals,
            runs_total=status.runs_total,
            successes_total=status.successes_total,
            failures_total=status.failures_total,
            recovering=status.recovering,
            max_attempts=status.max_attempts,
            current_attempt=status.current_attempt,
            retry_backoff_seconds=status.retry_backoff_seconds,
            retry_attempts_total=status.retry_attempts_total,
            overlap_skips_total=status.overlap_skips_total,
        )

    @classmethod
    def unavailable(
        cls,
        *,
        name: str,
        enabled: bool,
        interval_seconds: float,
        run_on_startup: bool,
        max_attempts: int,
        retry_backoff_seconds: float,
    ) -> "SchedulerStatusResponse":
        return cls(
            name=name,
            enabled=enabled,
            initialized=False,
            running=False,
            interval_seconds=interval_seconds,
            run_on_startup=run_on_startup,
            started_at=None,
            next_run_at=None,
            last_started_at=None,
            last_completed_at=None,
            last_success_at=None,
            last_failure_at=None,
            last_error=None,
            last_impact_score=None,
            last_arrivals=None,
            runs_total=0,
            successes_total=0,
            failures_total=0,
            recovering=False,
            max_attempts=max_attempts,
            current_attempt=None,
            retry_backoff_seconds=(retry_backoff_seconds),
            retry_attempts_total=0,
            overlap_skips_total=0,
        )
