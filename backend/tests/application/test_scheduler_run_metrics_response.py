from datetime import UTC, datetime, timedelta

from app.application.dto import SchedulerRunMetricsResponse
from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerRunMetrics,
)


def test_scheduler_metrics_response_maps_metrics() -> None:
    ended_at = datetime(
        2026,
        7,
        14,
        11,
        19,
        tzinfo=UTC,
    )

    started_at = ended_at - timedelta(days=7)

    metrics = SchedulerRunMetrics(
        scheduler_name="airport-signal-scheduler",
        window=SchedulerMetricsWindow.DAYS_7,
        window_started_at=started_at,
        window_ended_at=ended_at,
        total_runs=10,
        successful_runs=9,
        failed_runs=1,
        average_duration_ms=1500.55,
        average_attempts=1.2,
        total_retry_attempts=2,
        last_run_at=ended_at,
        last_success_at=ended_at,
        last_failure_at=None,
    )

    response = SchedulerRunMetricsResponse.from_metrics(metrics)

    assert response.scheduler_name == ("airport-signal-scheduler")
    assert response.window == "7d"
    assert response.window_started_at == started_at
    assert response.window_ended_at == ended_at
    assert response.total_runs == 10
    assert response.successful_runs == 9
    assert response.failed_runs == 1
    assert response.success_rate_percent == 90.0
    assert response.average_duration_ms == 1500.55
    assert response.average_attempts == 1.2
    assert response.total_retry_attempts == 2
