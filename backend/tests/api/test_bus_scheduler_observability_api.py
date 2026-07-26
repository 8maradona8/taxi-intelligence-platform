from datetime import UTC, datetime, timedelta

from fastapi.testclient import TestClient

from app.api.dependencies import (
    get_scheduler_configuration,
    get_scheduler_run_history_service,
    get_scheduler_runtime,
)
from app.application.interfaces import (
    BUS_SCHEDULER,
    SchedulerConfiguration,
    SchedulerFailureBreakdown,
    SchedulerFailureGroup,
    SchedulerMetricsWindow,
    SchedulerReliabilityTrend,
    SchedulerReliabilityTrendPoint,
    SchedulerRunMetrics,
    SchedulerTrendGranularity,
)
from app.main import app
from app.models.scheduler_run import SchedulerRun
from app.schedulers import BusSchedulerStatus


class FakeBusRuntime:
    @property
    def status(self) -> BusSchedulerStatus:
        now = datetime.now(UTC)

        return BusSchedulerStatus(
            name=BUS_SCHEDULER.name,
            running=True,
            interval_seconds=300,
            run_on_startup=True,
            started_at=now,
            next_run_at=now + timedelta(minutes=5),
            last_started_at=now,
            last_completed_at=now,
            last_success_at=now,
            last_failure_at=None,
            last_error=None,
            last_impact_score=38.0,
            last_arrivals=3,
            runs_total=12,
            successes_total=11,
            failures_total=1,
            recovering=False,
            max_attempts=2,
            current_attempt=None,
            retry_backoff_seconds=2.0,
            retry_attempts_total=1,
            overlap_skips_total=0,
        )


class FakeBusObservabilityHistoryService:
    @property
    def scheduler_identity(self):
        return BUS_SCHEDULER

    async def get_runs(
        self,
        *,
        limit: int = 20,
    ) -> list[SchedulerRun]:
        assert limit == 5

        started_at = datetime(
            2026,
            7,
            20,
            21,
            39,
            59,
            tzinfo=UTC,
        )

        completed_at = started_at + timedelta(
            milliseconds=143.76,
        )

        return [
            SchedulerRun(
                id=31,
                scheduler_name=BUS_SCHEDULER.name,
                status="success",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=143.76,
                attempts=1,
                retry_attempts=0,
                impact_score=13.0,
                arrivals=1,
                error_type=None,
                error_message=None,
            )
        ]

    async def get_metrics(
        self,
        *,
        window: SchedulerMetricsWindow = SchedulerMetricsWindow.HOURS_24,
        now: datetime | None = None,
    ) -> SchedulerRunMetrics:
        assert window == SchedulerMetricsWindow.DAYS_7

        ended_at = now or datetime(
            2026,
            7,
            21,
            0,
            0,
            tzinfo=UTC,
        )

        return SchedulerRunMetrics(
            scheduler_name=BUS_SCHEDULER.name,
            window=window,
            window_started_at=ended_at - timedelta(days=7),
            window_ended_at=ended_at,
            total_runs=12,
            successful_runs=11,
            failed_runs=1,
            average_duration_ms=182.5,
            average_attempts=1.08,
            total_retry_attempts=1,
            last_run_at=ended_at,
            last_success_at=ended_at,
            last_failure_at=ended_at - timedelta(days=1),
        )

    async def get_failure_breakdown(
        self,
        *,
        window: SchedulerMetricsWindow = SchedulerMetricsWindow.HOURS_24,
        now: datetime | None = None,
    ) -> SchedulerFailureBreakdown:
        assert window == SchedulerMetricsWindow.DAYS_7

        ended_at = now or datetime(
            2026,
            7,
            21,
            0,
            0,
            tzinfo=UTC,
        )

        return SchedulerFailureBreakdown(
            scheduler_name=BUS_SCHEDULER.name,
            window=window,
            window_started_at=ended_at - timedelta(days=7),
            window_ended_at=ended_at,
            total_failures=1,
            failures=[
                SchedulerFailureGroup(
                    error_type="HttpTimeoutError",
                    count=1,
                    last_occurred_at=ended_at - timedelta(days=1),
                    latest_message="Bus timetable request timed out",
                )
            ],
        )

    async def get_reliability_trend(
        self,
        *,
        window: SchedulerMetricsWindow,
        granularity: SchedulerTrendGranularity | None = None,
        now: datetime | None = None,
    ) -> SchedulerReliabilityTrend:
        assert window == SchedulerMetricsWindow.DAYS_7
        assert granularity == SchedulerTrendGranularity.DAY

        ended_at = now or datetime(
            2026,
            7,
            21,
            0,
            0,
            tzinfo=UTC,
        )

        period_started_at = ended_at.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        return SchedulerReliabilityTrend(
            scheduler_name=BUS_SCHEDULER.name,
            window=window,
            granularity=SchedulerTrendGranularity.DAY,
            window_started_at=ended_at - timedelta(days=7),
            window_ended_at=ended_at,
            points=[
                SchedulerReliabilityTrendPoint(
                    period_started_at=period_started_at,
                    total_runs=4,
                    successful_runs=3,
                    failed_runs=1,
                    average_duration_ms=190.0,
                    average_attempts=1.25,
                    total_retry_attempts=1,
                )
            ],
        )


def override_bus_configuration() -> SchedulerConfiguration:
    return SchedulerConfiguration(
        identity=BUS_SCHEDULER,
        enabled=True,
        interval_seconds=300,
        run_on_startup=True,
        max_attempts=2,
        retry_backoff_seconds=2.0,
    )


def override_bus_runtime() -> FakeBusRuntime:
    return FakeBusRuntime()


async def override_bus_history_service():
    yield FakeBusObservabilityHistoryService()


def install_bus_dependency_overrides() -> None:
    app.dependency_overrides[get_scheduler_configuration] = override_bus_configuration

    app.dependency_overrides[get_scheduler_runtime] = override_bus_runtime

    app.dependency_overrides[get_scheduler_run_history_service] = (
        override_bus_history_service
    )


def remove_bus_dependency_overrides() -> None:
    app.dependency_overrides.pop(
        get_scheduler_configuration,
        None,
    )
    app.dependency_overrides.pop(
        get_scheduler_runtime,
        None,
    )
    app.dependency_overrides.pop(
        get_scheduler_run_history_service,
        None,
    )


def test_bus_scheduler_run_history_endpoint(
    api_client: TestClient,
) -> None:
    install_bus_dependency_overrides()

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/bus/runs",
            params={
                "limit": 5,
            },
        )
    finally:
        remove_bus_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert data["scheduler_name"] == "bus-signal-scheduler"
    assert data["count"] == 1

    run = data["runs"][0]

    assert run["id"] == 31
    assert run["status"] == "success"
    assert run["duration_ms"] == 143.76
    assert run["attempts"] == 1
    assert run["retry_attempts"] == 0
    assert run["impact_score"] == 13.0
    assert run["arrivals"] == 1
    assert run["error_type"] is None
    assert run["error_message"] is None


def test_bus_scheduler_metrics_endpoint(
    api_client: TestClient,
) -> None:
    install_bus_dependency_overrides()

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/bus/metrics",
            params={
                "window": "7d",
            },
        )
    finally:
        remove_bus_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert data["scheduler_name"] == "bus-signal-scheduler"
    assert data["window"] == "7d"
    assert data["total_runs"] == 12
    assert data["successful_runs"] == 11
    assert data["failed_runs"] == 1
    assert data["success_rate_percent"] == 91.67
    assert data["average_duration_ms"] == 182.5
    assert data["total_retry_attempts"] == 1


def test_bus_scheduler_failure_breakdown_endpoint(
    api_client: TestClient,
) -> None:
    install_bus_dependency_overrides()

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/bus/failures",
            params={
                "window": "7d",
            },
        )
    finally:
        remove_bus_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert data["scheduler_name"] == "bus-signal-scheduler"
    assert data["window"] == "7d"
    assert data["total_failures"] == 1
    assert data["distinct_error_types"] == 1

    failure = data["failures"][0]

    assert failure["error_type"] == "HttpTimeoutError"
    assert failure["count"] == 1
    assert failure["share_percent"] == 100.0
    assert failure["latest_message"] == ("Bus timetable request timed out")


def test_bus_scheduler_reliability_trend_endpoint(
    api_client: TestClient,
) -> None:
    install_bus_dependency_overrides()

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/bus/trends",
            params={
                "window": "7d",
                "granularity": "day",
            },
        )
    finally:
        remove_bus_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    assert data["scheduler_name"] == "bus-signal-scheduler"
    assert data["window"] == "7d"
    assert data["granularity"] == "day"
    assert data["point_count"] == 1

    point = data["points"][0]

    assert point["total_runs"] == 4
    assert point["successful_runs"] == 3
    assert point["failed_runs"] == 1
    assert point["success_rate_percent"] == 75.0
    assert point["total_retry_attempts"] == 1


def test_bus_scheduler_observability_overview_endpoint(
    api_client: TestClient,
) -> None:
    install_bus_dependency_overrides()

    try:
        response = api_client.get(
            "/api/v1/system/schedulers/bus/overview",
            params={
                "window": "7d",
                "granularity": "day",
            },
        )
    finally:
        remove_bus_dependency_overrides()

    assert response.status_code == 200

    data = response.json()

    scheduler = data["scheduler"]
    reliability = data["reliability"]
    failures = data["failures"]
    trend = data["trend"]

    assert scheduler["name"] == "bus-signal-scheduler"
    assert scheduler["enabled"] is True
    assert scheduler["initialized"] is True
    assert scheduler["running"] is True
    assert scheduler["last_arrivals"] == 3
    assert scheduler["last_impact_score"] == 38.0

    assert reliability["scheduler_name"] == ("bus-signal-scheduler")
    assert reliability["window"] == "7d"
    assert reliability["total_runs"] == 12
    assert reliability["success_rate_percent"] == 91.67

    assert failures["scheduler_name"] == ("bus-signal-scheduler")
    assert failures["total_failures"] == 1

    assert trend["scheduler_name"] == ("bus-signal-scheduler")
    assert trend["granularity"] == "day"
    assert trend["point_count"] == 1


def test_bus_scheduler_observability_rejects_invalid_window(
    api_client: TestClient,
) -> None:
    response = api_client.get(
        "/api/v1/system/schedulers/bus/overview",
        params={
            "window": "90d",
        },
    )

    assert response.status_code == 422
    assert response.json()["error"]["code"] == ("VALIDATION_ERROR")
