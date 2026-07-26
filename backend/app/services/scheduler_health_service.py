from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.schedulers import AirportSchedulerStatus


@dataclass(frozen=True)
class SchedulerHealth:
    status: str
    enabled: bool
    initialized: bool
    running: bool
    stale: bool
    message: str
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None
    runs_total: int
    successes_total: int
    failures_total: int


class SchedulerHealthService:
    def evaluate(
        self,
        *,
        enabled: bool,
        scheduler_status: AirportSchedulerStatus | None,
        now: datetime | None = None,
    ) -> SchedulerHealth:
        current_time = now or datetime.now(UTC)

        if not enabled:
            return SchedulerHealth(
                status="disabled",
                enabled=False,
                initialized=False,
                running=False,
                stale=False,
                message="Airport scheduler is disabled by configuration.",
                last_success_at=None,
                last_failure_at=None,
                last_error=None,
                runs_total=0,
                successes_total=0,
                failures_total=0,
            )

        if scheduler_status is None:
            return SchedulerHealth(
                status="unhealthy",
                enabled=True,
                initialized=False,
                running=False,
                stale=False,
                message="Airport scheduler is enabled but not initialized.",
                last_success_at=None,
                last_failure_at=None,
                last_error=None,
                runs_total=0,
                successes_total=0,
                failures_total=0,
            )

        if not scheduler_status.running:
            return self._from_status(
                scheduler_status,
                status="unhealthy",
                stale=False,
                message="Airport scheduler task is not running.",
            )

        if scheduler_status.last_completed_at is None:
            return self._from_status(
                scheduler_status,
                status="starting",
                stale=False,
                message="Airport scheduler is waiting for its first completed run.",
            )
        if scheduler_status.recovering:
            return self._from_status(
                scheduler_status,
                status="recovering",
                stale=False,
                message=("Airport scheduler is recovering from a temporary failure."),
            )

        stale_after = timedelta(
            seconds=max(
                scheduler_status.interval_seconds * 2,
                60.0,
            )
        )

        stale = current_time - scheduler_status.last_completed_at > stale_after

        latest_run_failed = scheduler_status.last_failure_at is not None and (
            scheduler_status.last_success_at is None
            or scheduler_status.last_failure_at > scheduler_status.last_success_at
        )

        if latest_run_failed:
            return self._from_status(
                scheduler_status,
                status="degraded",
                stale=stale,
                message="The latest airport scheduler run failed.",
            )

        if stale:
            return self._from_status(
                scheduler_status,
                status="degraded",
                stale=True,
                message="Airport scheduler data is stale.",
            )

        return self._from_status(
            scheduler_status,
            status="healthy",
            stale=False,
            message="Airport scheduler is running normally.",
        )

    @staticmethod
    def _from_status(
        scheduler_status: AirportSchedulerStatus,
        *,
        status: str,
        stale: bool,
        message: str,
    ) -> SchedulerHealth:
        return SchedulerHealth(
            status=status,
            enabled=True,
            initialized=True,
            running=scheduler_status.running,
            stale=stale,
            message=message,
            last_success_at=scheduler_status.last_success_at,
            last_failure_at=scheduler_status.last_failure_at,
            last_error=scheduler_status.last_error,
            runs_total=scheduler_status.runs_total,
            successes_total=scheduler_status.successes_total,
            failures_total=scheduler_status.failures_total,
        )
