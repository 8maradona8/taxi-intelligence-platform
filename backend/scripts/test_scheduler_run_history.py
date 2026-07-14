import asyncio
from datetime import timedelta

from app.database.session import AsyncSessionLocal
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore
from app.repositories import SchedulerRunRepository
from app.schedulers import AirportScheduler
from app.services.postgres_scheduler_run_recorder import (
    PostgresSchedulerRunRecorder,
)


async def fake_airport_job() -> SignalEvent:
    return SignalEvent(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        zone_name="Sofia Airport",
        impact_score=ImpactScore(36.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.MEDIUM,
        ttl=timedelta(minutes=15),
        payload={
            "airport": "SOF",
            "arrivals": 3,
        },
    )


async def main() -> None:
    scheduler = AirportScheduler(
        job=fake_airport_job,
        interval_seconds=300,
        run_on_startup=False,
        run_recorder=PostgresSchedulerRunRecorder(
            session_factory=AsyncSessionLocal,
        ),
    )

    await scheduler.run_once()

    async with AsyncSessionLocal() as session:
        repository = SchedulerRunRepository(session)

        runs = await repository.list_latest(
            scheduler_name=AirportScheduler.NAME,
            limit=5,
        )

    print("Scheduler runs:", len(runs))

    for run in runs:
        print("---")
        print("ID:", run.id)
        print("Status:", run.status)
        print("Duration ms:", run.duration_ms)
        print("Attempts:", run.attempts)
        print("Retry attempts:", run.retry_attempts)
        print("Impact:", run.impact_score)
        print("Arrivals:", run.arrivals)
        print("Error:", run.error_message)


if __name__ == "__main__":
    asyncio.run(main())
