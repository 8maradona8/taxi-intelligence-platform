from collections.abc import AsyncIterator

from fastapi import Depends

from app.api.dependencies.scheduler import (
    get_scheduler_identity,
)
from app.application.interfaces import (
    SchedulerIdentity,
)
from app.database.session import AsyncSessionLocal
from app.repositories import SchedulerRunRepository
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)


async def get_scheduler_run_history_service(
    scheduler_identity: SchedulerIdentity = Depends(get_scheduler_identity),
) -> AsyncIterator[SchedulerRunHistoryService]:
    async with AsyncSessionLocal() as session:
        yield SchedulerRunHistoryService(
            repository=SchedulerRunRepository(session),
            scheduler_identity=scheduler_identity,
        )
