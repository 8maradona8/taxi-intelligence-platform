from datetime import datetime, timedelta
from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_run_history_service,
)
from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerMetricsWindow,
    SchedulerReliabilityTrend,
    SchedulerRunMetrics,
    SchedulerTrendGranularity,
)
from app.main import app


class FakeOverviewHistoryService:
    async def get_metrics(
        self,
        *,
        window: SchedulerMetricsWindow,
        now: datetime,
    ) -> SchedulerRunMetrics:
        return SchedulerRunMetrics(
            scheduler_name="airport-signal-scheduler",
            window=window,
            window_started_at=now - timedelta(days=7),
            window_ended_at=now,
            total_runs=10,
            successful_runs=9,
            failed_runs=1,
            average_duration_ms=1500.0,
            average_attempts=1.1,
            total_retry_attempts=1,
            last_run_at=now,
            last_success_at=now,
            last_failure_at=None,
        )

    async def get_failure_breakdown(
        self,
        *,
        window: SchedulerMetricsWindow,
        now: datetime,
    ) -> SchedulerFailureBreakdown:
        return SchedulerFailureBreakdown(
            scheduler_name="airport-signal-scheduler",
            window=window,
            window_started_at=now - timedelta(days=7),
            window_ended_at=now,
            total_failures=0,
            failures=[],
        )

    async def get_reliability_trend(
        self,
        *,
        window: SchedulerMetricsWindow,
        granularity: SchedulerTrendGranularity | None,
        now: datetime,
    ) -> SchedulerReliabilityTrend:
        return SchedulerReliabilityTrend(
            scheduler_name="airport-signal-scheduler",
            window=window,
            granularity=(granularity or SchedulerTrendGranularity.DAY),
            window_started_at=now - timedelta(days=7),
            window_ended_at=now,
            points=[],
        )


def test_scheduler_overview_endpoint(
    api_client: TestClient,
) -> None:
    async def override_history_service():
        yield FakeOverviewHistoryService()

    app.dependency_overrides[get_scheduler_run_history_service] = (
        override_history_service
    )

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/airport/overview",
            params={
                "window": "7d",
                "granularity": "day",
            },
        )
    finally:
        app.dependency_overrides.pop(
            get_scheduler_run_history_service,
            None,
        )

    assert response.status_code == 200

    data = response.json()

    assert data["scheduler"]["name"] == ("airport-signal-scheduler")
    assert data["reliability"]["window"] == "7d"
    assert data["reliability"]["total_runs"] == 10
    assert data["reliability"]["success_rate_percent"] == 90.0
    assert data["failures"]["total_failures"] == 0
    assert data["trend"]["granularity"] == "day"


def test_scheduler_overview_rejects_invalid_window(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/v1/system/schedulers/airport/overview",
        params={
            "window": "90d",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
