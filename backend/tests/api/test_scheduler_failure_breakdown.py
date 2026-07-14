from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_run_history_service,
)
from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerFailureGroup,
    SchedulerMetricsWindow,
)
from app.main import app


class FakeFailureBreakdownService:
    async def get_airport_failure_breakdown(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
    ) -> SchedulerFailureBreakdown:
        assert window == SchedulerMetricsWindow.DAYS_7

        ended_at = datetime(
            2026,
            7,
            14,
            12,
            0,
            tzinfo=UTC,
        )

        return SchedulerFailureBreakdown(
            scheduler_name=("airport-signal-scheduler"),
            window=window,
            window_started_at=(ended_at - timedelta(days=7)),
            window_ended_at=ended_at,
            total_failures=3,
            failures=[
                SchedulerFailureGroup(
                    error_type="HttpTimeoutError",
                    count=2,
                    last_occurred_at=ended_at,
                    latest_message=("Request timed out"),
                ),
                SchedulerFailureGroup(
                    error_type="HttpResponseError",
                    count=1,
                    last_occurred_at=ended_at,
                    latest_message="HTTP 503",
                ),
            ],
        )


def test_scheduler_failure_breakdown_endpoint(
    api_client: TestClient,
) -> None:
    async def override_service():
        yield FakeFailureBreakdownService()

    app.dependency_overrides[get_scheduler_run_history_service] = override_service

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/airport/failures",
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

    assert data["window"] == "7d"
    assert data["total_failures"] == 3
    assert data["distinct_error_types"] == 2
    assert data["failures"][0]["count"] == 2
    assert data["failures"][0]["share_percent"] == 66.67


def test_scheduler_failure_breakdown_rejects_invalid_window(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/v1/system/schedulers/airport/failures",
        params={
            "window": "90d",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
