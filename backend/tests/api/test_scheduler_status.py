from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.schedulers import AirportSchedulerStatus
from app.main import app


class FakeAirportScheduler:
    @property
    def status(self) -> AirportSchedulerStatus:
        now = datetime.now(UTC)

        return AirportSchedulerStatus(
            name="airport-signal-scheduler",
            running=True,
            interval_seconds=300,
            run_on_startup=True,
            started_at=now,
            next_run_at=now,
            last_started_at=now,
            last_completed_at=now,
            last_success_at=now,
            last_failure_at=None,
            last_error=None,
            last_impact_score=36.0,
            last_arrivals=3,
            runs_total=4,
            successes_total=4,
            failures_total=0,
        )


def test_airport_scheduler_status_endpoint(
    api_client: TestClient,
) -> None:
    previous_scheduler = getattr(
        app.state,
        "airport_scheduler",
        None,
    )

    app.state.airport_scheduler = FakeAirportScheduler()

    try:
        response = api_client.get("/api/v1/system/schedulers/airport")
    finally:
        app.state.airport_scheduler = previous_scheduler

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == ("airport-signal-scheduler")
    assert data["enabled"] is True
    assert data["initialized"] is True
    assert data["running"] is True
    assert data["interval_seconds"] == 300
    assert data["last_impact_score"] == 36.0
    assert data["last_arrivals"] == 3
    assert data["runs_total"] == 4
    assert data["successes_total"] == 4
    assert data["failures_total"] == 0
