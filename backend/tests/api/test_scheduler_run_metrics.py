from datetime import UTC, datetime

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_run_history_service,
)
from app.application.interfaces import SchedulerRunMetrics
from app.main import app


class FakeSchedulerMetricsService:
    async def get_airport_metrics(
        self,
    ) -> SchedulerRunMetrics:
        now = datetime(
            2026,
            7,
            14,
            11,
            19,
            tzinfo=UTC,
        )

        return SchedulerRunMetrics(
            scheduler_name="airport-signal-scheduler",
            total_runs=10,
            successful_runs=9,
            failed_runs=1,
            average_duration_ms=1500.55,
            average_attempts=1.2,
            total_retry_attempts=2,
            last_run_at=now,
            last_success_at=now,
            last_failure_at=None,
        )


def test_scheduler_run_metrics_endpoint(
    api_client: TestClient,
) -> None:
    async def override_metrics_service():
        yield FakeSchedulerMetricsService()

    app.dependency_overrides[get_scheduler_run_history_service] = (
        override_metrics_service
    )

    try:
        response = api_client.get("/api/v1/system/schedulers/airport/metrics")
    finally:
        app.dependency_overrides.pop(
            get_scheduler_run_history_service,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["scheduler_name"] == ("airport-signal-scheduler")
    assert data["total_runs"] == 10
    assert data["successful_runs"] == 9
    assert data["failed_runs"] == 1
    assert data["success_rate_percent"] == 90.0
    assert data["average_duration_ms"] == 1500.55
    assert data["average_attempts"] == 1.2
    assert data["total_retry_attempts"] == 2
