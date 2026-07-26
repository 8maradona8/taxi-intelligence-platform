import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.database.session import AsyncSessionLocal
from app.infrastructure.clients import (
    BdzLiveBoardClient,
)
from app.infrastructure.collectors import (
    SofiaRailwayCollector,
)
from app.infrastructure.http import AsyncHttpClient
from app.infrastructure.mappers import (
    RailwaySignalMapper,
    SofiaRailwayArrivalParser,
)
from app.repositories import (
    SignalRepository,
    ZoneRepository,
)
from app.services.railway_signal_persistence_service import (
    RailwaySignalPersistenceService,
)
from app.services.railway_signal_service import (
    RailwaySignalService,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


async def main() -> None:
    async with AsyncHttpClient(
        base_url="https://live.bdz.bg",
        timeout_seconds=20.0,
        max_retries=2,
        backoff_seconds=1.0,
        default_headers={
            "Accept": ("text/html,application/xhtml+xml"),
            "User-Agent": (
                "Taxi-Intelligence-Platform/0.1.0 (public railway data reader)"
            ),
        },
    ) as http_client:
        collector = SofiaRailwayCollector(
            client=BdzLiveBoardClient(
                http_client=http_client,
            ),
            parser=(SofiaRailwayArrivalParser()),
        )

        async with AsyncSessionLocal() as session:
            persistence_service = RailwaySignalPersistenceService(
                zone_repository=(ZoneRepository(session)),
                signal_repository=(SignalRepository(session)),
            )

            service = RailwaySignalService(
                collector=collector,
                signal_mapper=RailwaySignalMapper(),
                persistence_service=(persistence_service),
            )

            signal = await service.create_arrivals_signal(
                observed_at=datetime.now(SOFIA_TIMEZONE),
            )

    print("Zone:", signal.zone_name)
    print("Source:", signal.source.value)
    print("Type:", signal.signal_type.value)
    print("Impact:", signal.impact_score.value)
    print("Confidence:", signal.confidence.value)
    print("Priority:", signal.priority.value)
    print("Observed at:", signal.observed_at)
    print("Payload:", signal.payload)


if __name__ == "__main__":
    asyncio.run(main())
