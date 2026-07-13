from datetime import UTC, datetime, timedelta

from app.schedulers import AirportSchedulerStatus
from app.services.scheduler_health_service import (
    SchedulerHealthService,
)


def make_status(
    *,
    now: datetime,
    running: bool = True,
    last_completed_at: datetime | None = None,
    last_success_at: datetime | None = None,
    last_failure_at: datetime | None = None,
    last_error: str | None = None,
) -> AirportSchedulerStatus:
    return AirportSchedulerStatus(
        name="airport-signal-scheduler",
        running=running,
        interval_seconds=300,
        run_on_startup=True,
        started_at=now - timedelta(minutes=10),
        next_run_at=now + timedelta(minutes=5),
        last_started_at=last_completed_at,
        last_completed_at=last_completed_at,
        last_success_at=last_success_at,
        last_failure_at=last_failure_at,
        last_error=last_error,
        last_impact_score=24.0,
        last_arrivals=2,
        runs_total=3,
        successes_total=2,
        failures_total=1,
    )


def test_disabled_scheduler_is_reported_as_disabled() -> None:
    health = SchedulerHealthService().evaluate(
        enabled=False,
        scheduler_status=None,
    )

    assert health.status == "disabled"
    assert health.enabled is False
    assert health.running is False
    assert health.stale is False


def test_missing_enabled_scheduler_is_unhealthy() -> None:
    health = SchedulerHealthService().evaluate(
        enabled=True,
        scheduler_status=None,
    )

    assert health.status == "unhealthy"
    assert health.initialized is False


def test_running_scheduler_with_recent_success_is_healthy() -> None:
    now = datetime(
        2026,
        7,
        13,
        14,
        0,
        tzinfo=UTC,
    )

    completed_at = now - timedelta(minutes=2)

    health = SchedulerHealthService().evaluate(
        enabled=True,
        scheduler_status=make_status(
            now=now,
            last_completed_at=completed_at,
            last_success_at=completed_at,
        ),
        now=now,
    )

    assert health.status == "healthy"
    assert health.running is True
    assert health.stale is False


def test_latest_failed_run_is_degraded() -> None:
    now = datetime(
        2026,
        7,
        13,
        14,
        0,
        tzinfo=UTC,
    )

    success_at = now - timedelta(minutes=8)
    failure_at = now - timedelta(minutes=2)

    health = SchedulerHealthService().evaluate(
        enabled=True,
        scheduler_status=make_status(
            now=now,
            last_completed_at=failure_at,
            last_success_at=success_at,
            last_failure_at=failure_at,
            last_error="RuntimeError: source unavailable",
        ),
        now=now,
    )

    assert health.status == "degraded"
    assert health.last_error == ("RuntimeError: source unavailable")


def test_stale_scheduler_is_degraded() -> None:
    now = datetime(
        2026,
        7,
        13,
        14,
        0,
        tzinfo=UTC,
    )

    completed_at = now - timedelta(minutes=11)

    health = SchedulerHealthService().evaluate(
        enabled=True,
        scheduler_status=make_status(
            now=now,
            last_completed_at=completed_at,
            last_success_at=completed_at,
        ),
        now=now,
    )

    assert health.status == "degraded"
    assert health.stale is True
