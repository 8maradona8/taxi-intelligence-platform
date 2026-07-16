from fastapi.testclient import TestClient

from app.application.interfaces import AIRPORT_SCHEDULER
from app.main import app
from datetime import UTC, datetime

from app.schedulers import (
    AirportSchedulerStatus,
    SchedulerRegistry,
)


class FakeAirportRuntime:
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
            recovering=False,
            max_attempts=2,
            current_attempt=None,
            retry_backoff_seconds=2.0,
            retry_attempts_total=0,
            overlap_skips_total=0,
        )


def test_scheduler_registry_endpoint(
    api_client: TestClient,
) -> None:
    previous_registry = getattr(
        app.state,
        "scheduler_registry",
        None,
    )

    registry = SchedulerRegistry()

    registry.register(
        identity=AIRPORT_SCHEDULER,
        enabled=True,
        runtime=FakeAirportRuntime(),
    )

    app.state.scheduler_registry = registry

    try:
        response = api_client.get("/api/v1/system/schedulers")
    finally:
        app.state.scheduler_registry = previous_registry

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 1

    scheduler = data["schedulers"][0]

    assert scheduler["key"] == "airport"
    assert scheduler["name"] == ("airport-signal-scheduler")
    assert scheduler["enabled"] is True
    assert scheduler["initialized"] is True
    assert scheduler["running"] is True


def test_airport_status_keeps_legacy_app_state_support(
    api_client: TestClient,
) -> None:
    previous_registry = getattr(
        app.state,
        "scheduler_registry",
        None,
    )
    previous_scheduler = getattr(
        app.state,
        "airport_scheduler",
        None,
    )

    app.state.scheduler_registry = None
    app.state.airport_scheduler = FakeAirportRuntime()

    try:
        response = api_client.get("/api/v1/system/schedulers/airport")
    finally:
        app.state.scheduler_registry = previous_registry
        app.state.airport_scheduler = previous_scheduler

    assert response.status_code == 200
    assert response.json()["running"] is True
