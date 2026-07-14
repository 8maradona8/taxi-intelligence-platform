from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_run_history_service,
)
from app.main import app
from app.models.scheduler_run import SchedulerRun


class FakeSchedulerRunHistoryService:
    async def get_airport_runs(
        self,
        *,
        limit: int = 20,
    ) -> list[SchedulerRun]:
        assert limit == 5

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

        return [
            SchedulerRun(
                id=11,
                scheduler_name="airport-signal-scheduler",
                status="success",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=2000.0,
                attempts=1,
                retry_attempts=0,
                impact_score=24.0,
                arrivals=2,
                error_type=None,
                error_message=None,
            )
        ]


def test_scheduler_run_history_endpoint(
    api_client: TestClient,
) -> None:
    async def override_history_service():
        yield FakeSchedulerRunHistoryService()

    app.dependency_overrides[get_scheduler_run_history_service] = (
        override_history_service
    )

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/airport/runs",
            params={
                "limit": 5,
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_scheduler_run_history_service,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["scheduler_name"] == ("airport-signal-scheduler")
    assert data["count"] == 1

    run = data["runs"][0]

    assert run["id"] == 11
    assert run["status"] == "success"
    assert run["duration_ms"] == 2000.0
    assert run["attempts"] == 1
    assert run["retry_attempts"] == 0
    assert run["impact_score"] == 24.0
    assert run["arrivals"] == 2
    assert run["error_type"] is None


def test_scheduler_run_history_rejects_invalid_limit(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/v1/system/schedulers/airport/runs",
        params={
            "limit": 0,
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
