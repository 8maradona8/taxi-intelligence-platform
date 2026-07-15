from datetime import UTC, datetime, timedelta

import pytest

from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerMetricsWindow,
    SchedulerReliabilityTrend,
    SchedulerRunMetrics,
    SchedulerTrendGranularity,
)
from app.services.scheduler_observability_service import (
    SchedulerObservabilityService,
)


class FakeHistoryService:
    def __init__(self) -> None:
        self.received_times: list[datetime] = []

    async def get_airport_metrics(
        self,
        *,
        window: SchedulerMetricsWindow,
        now: datetime,
    ) -> SchedulerRunMetrics:
        self.received_times.append(now)

        return SchedulerRunMetrics(
            scheduler_name="airport-signal-scheduler",
            window=window,
            window_started_at=now - timedelta(hours=24),
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

    async def get_airport_failure_breakdown(
        self,
        *,
        window: SchedulerMetricsWindow,
        now: datetime,
    ) -> SchedulerFailureBreakdown:
        self.received_times.append(now)

        return SchedulerFailureBreakdown(
            scheduler_name="airport-signal-scheduler",
            window=window,
            window_started_at=now - timedelta(hours=24),
            window_ended_at=now,
            total_failures=0,
            failures=[],
        )

    async def get_airport_reliability_trend(
        self,
        *,
        window: SchedulerMetricsWindow,
        granularity: SchedulerTrendGranularity | None,
        now: datetime,
    ) -> SchedulerReliabilityTrend:
        self.received_times.append(now)

        return SchedulerReliabilityTrend(
            scheduler_name="airport-signal-scheduler",
            window=window,
            granularity=(granularity or SchedulerTrendGranularity.HOUR),
            window_started_at=now - timedelta(hours=24),
            window_ended_at=now,
            points=[],
        )


@pytest.mark.anyio
async def test_overview_uses_consistent_timestamp() -> None:
    history_service = FakeHistoryService()

    service = SchedulerObservabilityService(
        history_service=history_service,
    )

    now = datetime(
        2026,
        7,
        15,
        10,
        0,
        tzinfo=UTC,
    )

    overview = await service.get_airport_overview(
        scheduler=None,
        window=SchedulerMetricsWindow.HOURS_24,
        now=now,
    )

    assert overview.observed_at == now
    assert overview.scheduler_status is None

    assert history_service.received_times == [
        now,
        now,
        now,
    ]
