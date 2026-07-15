from datetime import UTC, datetime, timedelta

from app.application.dto import (
    SchedulerObservabilityOverviewResponse,
)
from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerMetricsWindow,
    SchedulerObservabilityOverview,
    SchedulerReliabilityTrend,
    SchedulerRunMetrics,
    SchedulerTrendGranularity,
)


def test_overview_response_maps_sections() -> None:
    now = datetime(
        2026,
        7,
        15,
        10,
        0,
        tzinfo=UTC,
    )

    overview = SchedulerObservabilityOverview(
        observed_at=now,
        scheduler_status=None,
        metrics=SchedulerRunMetrics(
            scheduler_name="airport-signal-scheduler",
            window=SchedulerMetricsWindow.HOURS_24,
            window_started_at=now - timedelta(hours=24),
            window_ended_at=now,
            total_runs=10,
            successful_runs=9,
            failed_runs=1,
            average_duration_ms=1500.0,
            average_attempts=1.1,
            total_retry_attempts=1,
            last_run_at=now,
            last_success_at=now,
            last_failure_at=None,
        ),
        failure_breakdown=SchedulerFailureBreakdown(
            scheduler_name="airport-signal-scheduler",
            window=SchedulerMetricsWindow.HOURS_24,
            window_started_at=now - timedelta(hours=24),
            window_ended_at=now,
            total_failures=0,
            failures=[],
        ),
        reliability_trend=SchedulerReliabilityTrend(
            scheduler_name="airport-signal-scheduler",
            window=SchedulerMetricsWindow.HOURS_24,
            granularity=SchedulerTrendGranularity.HOUR,
            window_started_at=now - timedelta(hours=24),
            window_ended_at=now,
            points=[],
        ),
    )

    response = SchedulerObservabilityOverviewResponse.from_overview(
        overview,
        scheduler_enabled=True,
        interval_seconds=300,
        run_on_startup=True,
        max_attempts=2,
        retry_backoff_seconds=2.0,
    )

    assert response.observed_at == now
    assert response.scheduler.initialized is False
    assert response.reliability.total_runs == 10
    assert response.reliability.success_rate_percent == 90.0
    assert response.failures.total_failures == 0
    assert response.trend.granularity == "hour"
    assert response.trend.point_count == 0
