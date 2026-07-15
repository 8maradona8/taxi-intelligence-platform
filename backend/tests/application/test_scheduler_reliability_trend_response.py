from datetime import UTC, datetime, timedelta

from app.application.dto import (
    SchedulerReliabilityTrendResponse,
)
from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerReliabilityTrend,
    SchedulerReliabilityTrendPoint,
    SchedulerTrendGranularity,
)


def test_trend_response_maps_points() -> None:
    ended_at = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    point_time = ended_at.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0,
    )

    trend = SchedulerReliabilityTrend(
        scheduler_name="airport-signal-scheduler",
        window=SchedulerMetricsWindow.DAYS_7,
        granularity=SchedulerTrendGranularity.DAY,
        window_started_at=(ended_at - timedelta(days=7)),
        window_ended_at=ended_at,
        points=[
            SchedulerReliabilityTrendPoint(
                period_started_at=point_time,
                total_runs=4,
                successful_runs=3,
                failed_runs=1,
                average_duration_ms=1820.4,
                average_attempts=1.25,
                total_retry_attempts=1,
            )
        ],
    )

    response = SchedulerReliabilityTrendResponse.from_trend(trend)

    assert response.window == "7d"
    assert response.granularity == "day"
    assert response.point_count == 1

    point = response.points[0]

    assert point.total_runs == 4
    assert point.successful_runs == 3
    assert point.failed_runs == 1
    assert point.success_rate_percent == 75.0
