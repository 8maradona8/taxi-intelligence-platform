from datetime import UTC, datetime

from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerFailureGroup,
    SchedulerMetricsWindow,
)


def test_failure_breakdown_calculates_shares() -> None:
    now = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    breakdown = SchedulerFailureBreakdown(
        scheduler_name="airport-signal-scheduler",
        window=SchedulerMetricsWindow.HOURS_24,
        window_started_at=None,
        window_ended_at=now,
        total_failures=3,
        failures=[
            SchedulerFailureGroup(
                error_type="HttpTimeoutError",
                count=2,
                last_occurred_at=now,
                latest_message="Request timed out",
            ),
            SchedulerFailureGroup(
                error_type="HttpResponseError",
                count=1,
                last_occurred_at=now,
                latest_message="HTTP 503",
            ),
        ],
    )

    assert breakdown.distinct_error_types == 2
    assert breakdown.share_percent(count=2) == 66.67
    assert breakdown.share_percent(count=1) == 33.33


def test_empty_failure_breakdown_has_zero_share() -> None:
    now = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    breakdown = SchedulerFailureBreakdown(
        scheduler_name="airport-signal-scheduler",
        window=SchedulerMetricsWindow.HOURS_24,
        window_started_at=None,
        window_ended_at=now,
        total_failures=0,
        failures=[],
    )

    assert breakdown.distinct_error_types == 0
    assert breakdown.share_percent(count=0) == 0.0
