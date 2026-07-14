import asyncio

from app.application.interfaces import (
    SchedulerMetricsWindow,
)
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

        for window in SchedulerMetricsWindow:
            metrics = await service.get_airport_metrics(window=window)

            print("=" * 40)
            print("Window:", metrics.window.value)
            print(
                "Window started:",
                metrics.window_started_at,
            )
            print(
                "Window ended:",
                metrics.window_ended_at,
            )
            print("Total runs:", metrics.total_runs)
            print(
                "Successful runs:",
                metrics.successful_runs,
            )
            print(
                "Failed runs:",
                metrics.failed_runs,
            )
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


if __name__ == "__main__":
    asyncio.run(main())
