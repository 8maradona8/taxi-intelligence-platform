import asyncio

from app.application.interfaces import (
    AIRPORT_SCHEDULER,
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
            scheduler_identity=AIRPORT_SCHEDULER,
        )

        for window in SchedulerMetricsWindow:
            trend = await service.get_reliability_trend(
                window=window,
            )

            print("=" * 50)
            print("Window:", trend.window.value)
            print(
                "Granularity:",
                trend.granularity.value,
            )
            print("Point count:", trend.point_count)

            for point in trend.points:
                print("---")
                print(
                    "Period:",
                    point.period_started_at,
                )
                print(
                    "Total runs:",
                    point.total_runs,
                )
                print(
                    "Successful:",
                    point.successful_runs,
                )
                print(
                    "Failed:",
                    point.failed_runs,
                )
                print(
                    "Success rate:",
                    point.success_rate_percent,
                )
                print(
                    "Average duration:",
                    point.average_duration_ms,
                )
                print(
                    "Retries:",
                    point.total_retry_attempts,
                )


if __name__ == "__main__":
    asyncio.run(main())
