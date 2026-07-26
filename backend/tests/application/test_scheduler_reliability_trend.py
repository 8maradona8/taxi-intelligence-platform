from datetime import UTC, datetime

from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerReliabilityTrend,
    SchedulerReliabilityTrendPoint,
    SchedulerTrendGranularity,
)


def test_trend_point_calculates_success_rate() -> None:
    point = SchedulerReliabilityTrendPoint(
        period_started_at=datetime(
            2026,
            7,
            14,
            tzinfo=UTC,
        ),
        total_runs=4,
        successful_runs=3,
        failed_runs=1,
        average_duration_ms=1200.0,
        average_attempts=1.25,
        total_retry_attempts=1,
    )

    assert point.success_rate_percent == 75.0


def test_empty_trend_point_has_zero_success_rate() -> None:
    point = SchedulerReliabilityTrendPoint(
        period_started_at=datetime(
            2026,
            7,
            14,
            tzinfo=UTC,
        ),
        total_runs=0,
        successful_runs=0,
        failed_runs=0,
        average_duration_ms=0.0,
        average_attempts=0.0,
        total_retry_attempts=0,
    )

    assert point.success_rate_percent == 0.0


def test_trend_reports_point_count() -> None:
    now = datetime(
        2026,
        7,
        14,
        tzinfo=UTC,
    )

    trend = SchedulerReliabilityTrend(
        scheduler_name="airport-signal-scheduler",
        window=SchedulerMetricsWindow.DAYS_7,
        granularity=SchedulerTrendGranularity.DAY,
        window_started_at=None,
        window_ended_at=now,
        points=[
            SchedulerReliabilityTrendPoint(
                period_started_at=now,
                total_runs=1,
                successful_runs=1,
                failed_runs=0,
                average_duration_ms=1000.0,
                average_attempts=1.0,
                total_retry_attempts=0,
            )
        ],
    )

    assert trend.point_count == 1


def test_24_hour_window_defaults_to_hour() -> None:
    assert (
        SchedulerTrendGranularity.default_for_window(SchedulerMetricsWindow.HOURS_24)
        == SchedulerTrendGranularity.HOUR
    )


def test_7_day_window_defaults_to_day() -> None:
    assert (
        SchedulerTrendGranularity.default_for_window(SchedulerMetricsWindow.DAYS_7)
        == SchedulerTrendGranularity.DAY
    )
