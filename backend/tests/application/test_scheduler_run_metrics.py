from app.application.interfaces import SchedulerRunMetrics


def test_scheduler_metrics_calculates_success_rate() -> None:
    metrics = SchedulerRunMetrics(
        scheduler_name="airport-signal-scheduler",
        total_runs=25,
        successful_runs=23,
        failed_runs=2,
        average_duration_ms=1650.4,
        average_attempts=1.08,
        total_retry_attempts=2,
        last_run_at=None,
        last_success_at=None,
        last_failure_at=None,
    )

    assert metrics.success_rate_percent == 92.0


def test_scheduler_metrics_returns_zero_rate_without_runs() -> None:
    metrics = SchedulerRunMetrics(
        scheduler_name="airport-signal-scheduler",
        total_runs=0,
        successful_runs=0,
        failed_runs=0,
        average_duration_ms=0.0,
        average_attempts=0.0,
        total_retry_attempts=0,
        last_run_at=None,
        last_success_at=None,
        last_failure_at=None,
    )

    assert metrics.success_rate_percent == 0.0
