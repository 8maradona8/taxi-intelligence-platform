from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.application.interfaces import (
    AIRPORT_SCHEDULER,
    BUS_SCHEDULER,
    RAILWAY_SCHEDULER,
)
from app.main import app
from app.schedulers import (
    AirportSchedulerStatus,
    SchedulerRegistry,
)


class FakeSchedulerRuntime:
    def __init__(
        self,
        *,
        name: str,
        impact_score: float,
        arrivals: int,
    ) -> None:
        self._name = name
        self._impact_score = impact_score
        self._arrivals = arrivals

    @property
    def status(self) -> AirportSchedulerStatus:
        now = datetime.now(UTC)

        return AirportSchedulerStatus(
            name=self._name,
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
            last_impact_score=self._impact_score,
            last_arrivals=self._arrivals,
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
        runtime=FakeSchedulerRuntime(
            name="airport-signal-scheduler",
            impact_score=24.0,
            arrivals=2,
        ),
    )

    registry.register(
        identity=BUS_SCHEDULER,
        enabled=True,
        runtime=FakeSchedulerRuntime(
            name="bus-signal-scheduler",
            impact_score=38.0,
            arrivals=3,
        ),
    )

    registry.register(
        identity=RAILWAY_SCHEDULER,
        enabled=True,
        runtime=FakeSchedulerRuntime(
            name="railway-signal-scheduler",
            impact_score=100.0,
            arrivals=8,
        ),
    )

    app.state.scheduler_registry = registry

    try:
        response = api_client.get("/api/v1/system/schedulers")
    finally:
        app.state.scheduler_registry = previous_registry

    assert response.status_code == 200

    data = response.json()

    assert data["count"] == 3

    schedulers = {scheduler["key"]: scheduler for scheduler in data["schedulers"]}

    assert set(schedulers) == {
        "airport",
        "bus",
        "railway",
    }

    assert schedulers["airport"] == {
        "key": "airport",
        "name": "airport-signal-scheduler",
        "enabled": True,
        "initialized": True,
        "running": True,
    }

    assert schedulers["bus"] == {
        "key": "bus",
        "name": "bus-signal-scheduler",
        "enabled": True,
        "initialized": True,
        "running": True,
    }

    assert schedulers["railway"] == {
        "key": "railway",
        "name": "railway-signal-scheduler",
        "enabled": True,
        "initialized": True,
        "running": True,
    }


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
    app.state.airport_scheduler = FakeSchedulerRuntime(
        name="airport-signal-scheduler",
        impact_score=24.0,
        arrivals=2,
    )

    try:
        response = api_client.get("/api/v1/system/schedulers/airport")
    finally:
        app.state.scheduler_registry = previous_registry
        app.state.airport_scheduler = previous_scheduler

    assert response.status_code == 200
    assert response.json()["running"] is True
