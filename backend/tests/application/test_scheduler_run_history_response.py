from datetime import UTC, datetime

from app.application.dto import SchedulerRunHistoryResponse
from app.models.scheduler_run import SchedulerRun


def test_scheduler_run_history_response_maps_models() -> None:
    started_at = datetime(
        2026,
        7,
        14,
        8,
        0,
        tzinfo=UTC,
    )

    completed_at = datetime(
        2026,
        7,
        14,
        8,
        0,
        2,
        tzinfo=UTC,
    )

    run = SchedulerRun(
        id=7,
        scheduler_name="airport-signal-scheduler",
        status="success",
        started_at=started_at,
        completed_at=completed_at,
        duration_ms=2000.0,
        attempts=2,
        retry_attempts=1,
        impact_score=36.0,
        arrivals=3,
        error_type=None,
        error_message=None,
    )

    response = SchedulerRunHistoryResponse.from_models(
        scheduler_name="airport-signal-scheduler",
        runs=[run],
    )

    assert response.scheduler_name == ("airport-signal-scheduler")
    assert response.count == 1

    item = response.runs[0]

    assert item.id == 7
    assert item.status == "success"
    assert item.duration_ms == 2000.0
    assert item.attempts == 2
    assert item.retry_attempts == 1
    assert item.impact_score == 36.0
    assert item.arrivals == 3
    assert item.error_type is None
    assert item.error_message is None
