from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_configuration,
    get_scheduler_runtime,
)
from app.application.interfaces import (
    BUS_SCHEDULER,
    SchedulerConfiguration,
)
from app.main import app
from app.schedulers import BusSchedulerStatus


class FakeBusRuntime:
    @property
    def status(
        self,
    ) -> BusSchedulerStatus:
        now = datetime.now(UTC)

        return BusSchedulerStatus(
            name="bus-signal-scheduler",
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
            last_impact_score=38.0,
            last_arrivals=3,
            runs_total=2,
            successes_total=2,
            failures_total=0,
            recovering=False,
            max_attempts=2,
            current_attempt=None,
            retry_backoff_seconds=2.0,
            retry_attempts_total=0,
            overlap_skips_total=0,
        )


def test_bus_scheduler_status_endpoint(
    api_client: TestClient,
) -> None:
    def override_configuration() -> SchedulerConfiguration:
        return SchedulerConfiguration(
            identity=BUS_SCHEDULER,
            enabled=True,
            interval_seconds=300,
            run_on_startup=True,
            max_attempts=2,
            retry_backoff_seconds=2.0,
        )

    def override_runtime() -> FakeBusRuntime:
        return FakeBusRuntime()

    app.dependency_overrides[get_scheduler_configuration] = override_configuration
    app.dependency_overrides[get_scheduler_runtime] = override_runtime

    try:
        response = api_client.get("/api/v1/system/schedulers/bus")
    finally:
        app.dependency_overrides.pop(
            get_scheduler_configuration,
            None,
        )
        app.dependency_overrides.pop(
            get_scheduler_runtime,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["name"] == "bus-signal-scheduler"
    assert data["enabled"] is True
    assert data["initialized"] is True
    assert data["running"] is True
    assert data["interval_seconds"] == 300
    assert data["last_arrivals"] == 3
    assert data["last_impact_score"] == 38.0
