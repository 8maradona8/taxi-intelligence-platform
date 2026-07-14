import asyncio

from app.database.session import AsyncSessionLocal
from app.repositories import SchedulerRunRepository
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)


async def main() -> None:
    async with AsyncSessionLocal() as session:
        service = SchedulerRunHistoryService(
            repository=SchedulerRunRepository(session),
        )

        metrics = await service.get_airport_metrics()

    print("Scheduler:", metrics.scheduler_name)
    print("Total runs:", metrics.total_runs)
    print("Successful runs:", metrics.successful_runs)
    print("Failed runs:", metrics.failed_runs)
    print(
        "Success rate:",
        metrics.success_rate_percent,
    )
    print(
        "Average duration ms:",
        metrics.average_duration_ms,
    )
    print(
        "Average attempts:",
        metrics.average_attempts,
    )
    print(
        "Total retry attempts:",
        metrics.total_retry_attempts,
    )
    print("Last run:", metrics.last_run_at)
    print("Last success:", metrics.last_success_at)
    print("Last failure:", metrics.last_failure_at)


if __name__ == "__main__":
    asyncio.run(main())
