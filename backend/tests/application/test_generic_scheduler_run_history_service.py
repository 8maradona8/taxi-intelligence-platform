from datetime import UTC, datetime

import pytest

from app.application.interfaces import (
    SchedulerIdentity,
    SchedulerMetricsWindow,
    SchedulerRunMetrics,
)
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)


class FakeSchedulerRunRepository:
    def __init__(self) -> None:
        self.received_scheduler_name: str | None = None

    async def get_metrics(
        self,
        *,
        scheduler_name: str,
        window: SchedulerMetricsWindow,
        window_started_at: datetime | None,
        window_ended_at: datetime,
    ) -> SchedulerRunMetrics:
        self.received_scheduler_name = scheduler_name

        return SchedulerRunMetrics(
            scheduler_name=scheduler_name,
            window=window,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
            total_runs=0,
            successful_runs=0,
            failed_runs=0,
            average_duration_ms=0.0,
            average_attempts=0.0,
            total_retry_attempts=0,
            last_run_at=None,
            last_success_at=None,
            last_failure_at=None,
        )


@pytest.mark.anyio
async def test_history_service_uses_injected_identity() -> None:
    repository = FakeSchedulerRunRepository()

    service = SchedulerRunHistoryService(
        repository=repository,  # type: ignore[arg-type]
        scheduler_identity=SchedulerIdentity(
            key="weather",
            name="weather-signal-scheduler",
        ),
    )

    metrics = await service.get_metrics(
        window=SchedulerMetricsWindow.HOURS_24,
        now=datetime(
            2026,
            7,
            15,
            12,
            0,
            tzinfo=UTC,
        ),
    )

    assert repository.received_scheduler_name == ("weather-signal-scheduler")
    assert metrics.scheduler_name == ("weather-signal-scheduler")
