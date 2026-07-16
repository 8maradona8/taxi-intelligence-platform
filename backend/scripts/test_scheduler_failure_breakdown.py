import asyncio

from app.application.interfaces import (
    SchedulerMetricsWindow,
)
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

        breakdown = await service.get_airport_failure_breakdown(
            window=SchedulerMetricsWindow.ALL
        )

    print("Scheduler:", breakdown.scheduler_name)
    print("Window:", breakdown.window.value)
    print("Total failures:", breakdown.total_failures)
    print(
        "Distinct error types:",
        breakdown.distinct_error_types,
    )

    for failure in breakdown.failures:
        print("---")
        print("Error type:", failure.error_type)
        print("Count:", failure.count)
        print(
            "Share:",
            breakdown.share_percent(count=failure.count),
        )
        print(
            "Last occurred:",
            failure.last_occurred_at,
        )
        print(
            "Latest message:",
            failure.latest_message,
        )


if __name__ == "__main__":
    asyncio.run(main())
