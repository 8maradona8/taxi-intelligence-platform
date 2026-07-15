from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_run_history_service,
)
from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerReliabilityTrend,
    SchedulerReliabilityTrendPoint,
    SchedulerTrendGranularity,
)
from app.main import app


class FakeTrendService:
    async def get_airport_reliability_trend(
        self,
        *,
        window: SchedulerMetricsWindow,
        granularity: (SchedulerTrendGranularity | None) = None,
    ) -> SchedulerReliabilityTrend:
        assert window == SchedulerMetricsWindow.DAYS_7
        assert granularity == SchedulerTrendGranularity.DAY

        ended_at = datetime(
            2026,
            7,
            14,
            12,
            0,
            tzinfo=UTC,
        )

        return SchedulerReliabilityTrend(
            scheduler_name=("airport-signal-scheduler"),
            window=window,
            granularity=granularity,
            window_started_at=(ended_at - timedelta(days=7)),
            window_ended_at=ended_at,
            points=[
                SchedulerReliabilityTrendPoint(
                    period_started_at=ended_at.replace(
                        hour=0,
                        minute=0,
                        second=0,
                        microsecond=0,
                    ),
                    total_runs=4,
                    successful_runs=3,
                    failed_runs=1,
                    average_duration_ms=1820.4,
                    average_attempts=1.25,
                    total_retry_attempts=1,
                )
            ],
        )


def test_scheduler_reliability_trend_endpoint(
    api_client: TestClient,
) -> None:
    async def override_service():
        yield FakeTrendService()

    app.dependency_overrides[get_scheduler_run_history_service] = override_service

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/airport/trends",
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

    assert data["window"] == "7d"
    assert data["granularity"] == "day"
    assert data["point_count"] == 1
    assert data["points"][0]["total_runs"] == 4
    assert data["points"][0]["success_rate_percent"] == 75.0


def test_scheduler_trend_rejects_invalid_granularity(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/v1/system/schedulers/airport/trends",
        params={
            "granularity": "week",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
