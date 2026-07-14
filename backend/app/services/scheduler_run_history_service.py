from app.application.interfaces import SchedulerRunMetrics
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
    ) -> SchedulerRunMetrics:
        return await self._repository.get_metrics(
            scheduler_name=AirportScheduler.NAME,
        )
