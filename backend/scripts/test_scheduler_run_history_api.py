import asyncio

from app.database.session import AsyncSessionLocal
from app.repositories import SchedulerRunRepository
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)
from app.application.interfaces import (
    AIRPORT_SCHEDULER,
)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        service = SchedulerRunHistoryService(
            repository=SchedulerRunRepository(session),
            scheduler_identity=AIRPORT_SCHEDULER,
        )

        runs = await service.get_airport_runs(
            limit=10,
        )

    print("Scheduler runs:", len(runs))

    for run in runs:
        print("---")
        print("ID:", run.id)
        print("Status:", run.status)
        print("Started:", run.started_at)
        print("Completed:", run.completed_at)
        print("Duration ms:", run.duration_ms)
        print("Attempts:", run.attempts)
        print("Retry attempts:", run.retry_attempts)
        print("Impact:", run.impact_score)
        print("Arrivals:", run.arrivals)
        print("Error type:", run.error_type)
        print("Error message:", run.error_message)


if __name__ == "__main__":
    asyncio.run(main())
