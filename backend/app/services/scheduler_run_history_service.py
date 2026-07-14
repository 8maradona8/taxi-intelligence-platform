from datetime import UTC, datetime

from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerRunMetrics,
)
from app.models.scheduler_run import SchedulerRun
from app.repositories import SchedulerRunRepository
from app.schedulers import AirportScheduler


class SchedulerRunHistoryService:
    def __init__(
        self,
        *,
        repository: SchedulerRunRepository,
    ) -> None:
        self._repository = repository

    async def get_airport_runs(
        self,
        *,
        limit: int = 20,
    ) -> list[SchedulerRun]:
        return await self._repository.list_latest(
            scheduler_name=AirportScheduler.NAME,
            limit=limit,
        )

    async def get_airport_metrics(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        now: datetime | None = None,
    ) -> SchedulerRunMetrics:
        window_ended_at = now or datetime.now(UTC)

        if window_ended_at.tzinfo is None:
            window_ended_at = window_ended_at.replace(tzinfo=UTC)

        window_started_at = window.started_at(ended_at=window_ended_at)

        return await self._repository.get_metrics(
            scheduler_name=AirportScheduler.NAME,
            window=window,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
        )
