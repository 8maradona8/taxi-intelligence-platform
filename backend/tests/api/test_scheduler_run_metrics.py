from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_run_history_service,
)
from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerRunMetrics,
)
from app.main import app


class FakeSchedulerMetricsService:
    async def get_metrics(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
    ) -> SchedulerRunMetrics:
        assert window == SchedulerMetricsWindow.DAYS_7

        ended_at = datetime(
            2026,
            7,
            14,
            11,
            19,
            tzinfo=UTC,
        )

        return SchedulerRunMetrics(
            scheduler_name="airport-signal-scheduler",
            window=window,
            window_started_at=(ended_at - timedelta(days=7)),
            window_ended_at=ended_at,
            total_runs=10,
            successful_runs=9,
            failed_runs=1,
            average_duration_ms=1500.55,
            average_attempts=1.2,
            total_retry_attempts=2,
            last_run_at=ended_at,
            last_success_at=ended_at,
            last_failure_at=None,
        )


def test_scheduler_run_metrics_endpoint_supports_window(
    api_client: TestClient,
) -> None:
    async def override_metrics_service():
        yield FakeSchedulerMetricsService()

    app.dependency_overrides[get_scheduler_run_history_service] = (
        override_metrics_service
    )

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/airport/metrics",
            params={
                "window": "7d",
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
    assert data["window"] == "7d"
    assert data["window_started_at"] is not None
    assert data["window_ended_at"] is not None
    assert data["total_runs"] == 10
    assert data["successful_runs"] == 9
    assert data["failed_runs"] == 1
    assert data["success_rate_percent"] == 90.0


def test_scheduler_run_metrics_rejects_invalid_window(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/v1/system/schedulers/airport/metrics",
        params={
            "window": "90d",
        },
    )

    assert response.status_code == 422

    data = response.json()

    assert data["error"]["code"] == "VALIDATION_ERROR"
