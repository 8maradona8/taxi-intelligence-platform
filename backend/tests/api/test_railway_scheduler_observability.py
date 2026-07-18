from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.main import app
from app.schedulers import (
    RailwaySchedulerStatus,
    SchedulerRegistry,
)
from app.application.interfaces import (
    AIRPORT_SCHEDULER,
    RAILWAY_SCHEDULER,
    SchedulerConfiguration,
)
from app.api.dependencies import (
    get_scheduler_configuration,
    get_scheduler_runtime,
)


class FakeRailwayRuntime:
    @property
    def status(
        self,
    ) -> RailwaySchedulerStatus:
        now = datetime.now(UTC)

        return RailwaySchedulerStatus(
            name="railway-signal-scheduler",
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
            last_impact_score=100.0,
            last_arrivals=8,
            runs_total=3,
            successes_total=3,
            failures_total=0,
            recovering=False,
            max_attempts=2,
            current_attempt=None,
            retry_backoff_seconds=2.0,
            retry_attempts_total=0,
            overlap_skips_total=0,
        )


def install_registry() -> object:
    previous_registry = getattr(
        app.state,
        "scheduler_registry",
        None,
    )

    registry = SchedulerRegistry()

    registry.register(
        identity=AIRPORT_SCHEDULER,
        enabled=True,
    )
    registry.register(
        identity=RAILWAY_SCHEDULER,
        enabled=True,
        runtime=FakeRailwayRuntime(),
    )

    app.state.scheduler_registry = registry

    return previous_registry


def test_railway_scheduler_status_endpoint(
    api_client: TestClient,
) -> None:
    def override_configuration() -> SchedulerConfiguration:
        return SchedulerConfiguration(
            identity=RAILWAY_SCHEDULER,
            enabled=True,
            interval_seconds=300,
            run_on_startup=True,
            max_attempts=2,
            retry_backoff_seconds=2.0,
        )

    def override_runtime() -> FakeRailwayRuntime:
        return FakeRailwayRuntime()

    app.dependency_overrides[get_scheduler_configuration] = override_configuration
    app.dependency_overrides[get_scheduler_runtime] = override_runtime

    try:
        response = api_client.get("/api/v1/system/schedulers/railway")
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

    assert data["name"] == "railway-signal-scheduler"
    assert data["enabled"] is True
    assert data["initialized"] is True
    assert data["running"] is True
    assert data["interval_seconds"] == 300
    assert data["last_arrivals"] == 8
    assert data["last_impact_score"] == 100.0


def test_unknown_scheduler_returns_404(
    api_client: TestClient,
) -> None:
    previous_registry = install_registry()

    try:
        response = api_client.get("/api/v1/system/schedulers/metro")
    finally:
        app.state.scheduler_registry = previous_registry

    assert response.status_code == 404
