from datetime import UTC, datetime, timedelta

from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerRunMetrics,
)


def make_metrics(
    *,
    total_runs: int,
    successful_runs: int,
) -> SchedulerRunMetrics:
    ended_at = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    return SchedulerRunMetrics(
        scheduler_name="airport-signal-scheduler",
        window=SchedulerMetricsWindow.HOURS_24,
        window_started_at=(ended_at - timedelta(hours=24)),
        window_ended_at=ended_at,
        total_runs=total_runs,
        successful_runs=successful_runs,
        failed_runs=total_runs - successful_runs,
        average_duration_ms=1650.4,
        average_attempts=1.08,
        total_retry_attempts=2,
        last_run_at=None,
        last_success_at=None,
        last_failure_at=None,
    )


def test_scheduler_metrics_calculates_success_rate() -> None:
    metrics = make_metrics(
        total_runs=25,
        successful_runs=23,
    )

    assert metrics.success_rate_percent == 92.0


def test_scheduler_metrics_returns_zero_rate_without_runs() -> None:
    metrics = make_metrics(
        total_runs=0,
        successful_runs=0,
    )

    assert metrics.success_rate_percent == 0.0


def test_metrics_window_calculates_24_hour_start() -> None:
    ended_at = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    started_at = SchedulerMetricsWindow.HOURS_24.started_at(ended_at=ended_at)

    assert started_at == (ended_at - timedelta(hours=24))


def test_metrics_window_calculates_7_day_start() -> None:
    ended_at = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    started_at = SchedulerMetricsWindow.DAYS_7.started_at(ended_at=ended_at)

    assert started_at == (ended_at - timedelta(days=7))


def test_metrics_window_all_has_no_start() -> None:
    ended_at = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    assert SchedulerMetricsWindow.ALL.started_at(ended_at=ended_at) is None
