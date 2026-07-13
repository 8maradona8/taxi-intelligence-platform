from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.schedulers import AirportSchedulerStatus


class FakeHealthyAirportScheduler:
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
            last_impact_score=24.0,
            last_arrivals=2,
            runs_total=1,
            successes_total=1,
            failures_total=0,
        )


def test_system_health_includes_scheduler(
    api_client: TestClient,
) -> None:
    previous_scheduler = getattr(
        app.state,
        "airport_scheduler",
        None,
    )

    app.state.airport_scheduler = FakeHealthyAirportScheduler()

    try:
        response = api_client.get("/api/v1/system/health")
    finally:
        app.state.airport_scheduler = previous_scheduler

    assert response.status_code == 200

    data = response.json()

    assert data["status"] == "healthy"
    assert data["database"]["connected"] is True

    scheduler = data["airport_scheduler"]

    assert scheduler["status"] == "healthy"
    assert scheduler["enabled"] is True
    assert scheduler["initialized"] is True
    assert scheduler["running"] is True
    assert scheduler["stale"] is False
    assert scheduler["runs_total"] == 1
    assert scheduler["successes_total"] == 1
    assert scheduler["failures_total"] == 0
