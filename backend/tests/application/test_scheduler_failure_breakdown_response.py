from datetime import UTC, datetime, timedelta

from app.application.dto import (
    SchedulerFailureBreakdownResponse,
)
from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerFailureGroup,
    SchedulerMetricsWindow,
)


def test_failure_breakdown_response_maps_groups() -> None:
    ended_at = datetime(
        2026,
        7,
        14,
        12,
        0,
        tzinfo=UTC,
    )

    breakdown = SchedulerFailureBreakdown(
        scheduler_name="airport-signal-scheduler",
        window=SchedulerMetricsWindow.DAYS_7,
        window_started_at=(ended_at - timedelta(days=7)),
        window_ended_at=ended_at,
        total_failures=3,
        failures=[
            SchedulerFailureGroup(
                error_type="HttpTimeoutError",
                count=2,
                last_occurred_at=ended_at,
                latest_message="Request timed out",
            )
        ],
    )

    response = SchedulerFailureBreakdownResponse.from_breakdown(breakdown)

    assert response.scheduler_name == ("airport-signal-scheduler")
    assert response.window == "7d"
    assert response.total_failures == 3
    assert response.distinct_error_types == 1

    failure = response.failures[0]

    assert failure.error_type == "HttpTimeoutError"
    assert failure.count == 2
    assert failure.share_percent == 66.67
    assert failure.latest_message == "Request timed out"
