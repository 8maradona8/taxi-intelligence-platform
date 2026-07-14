from collections.abc import AsyncIterator

from app.database.session import AsyncSessionLocal
from app.repositories import SchedulerRunRepository
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)


async def get_scheduler_run_history_service() -> AsyncIterator[
    SchedulerRunHistoryService
]:
    async with AsyncSessionLocal() as session:
        yield SchedulerRunHistoryService(
            repository=SchedulerRunRepository(session),
        )
