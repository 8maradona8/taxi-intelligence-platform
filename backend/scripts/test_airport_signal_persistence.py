import asyncio
from datetime import datetime
from zoneinfo import ZoneInfo

from app.database.session import AsyncSessionLocal
from app.infrastructure.clients import SofiaAirportWebsiteClient
from app.infrastructure.collectors import SofiaAirportCollector
from app.infrastructure.http import AsyncHttpClient
from app.infrastructure.mappers import (
    AirportSignalMapper,
    SofiaAirportFlightParser,
)
from app.repositories import SignalRepository, ZoneRepository
from app.services.airport_signal_persistence_service import (
    AirportSignalPersistenceService,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


async def main() -> None:
    async with AsyncHttpClient(
        base_url="https://sofia-airport.eu",
        timeout_seconds=20.0,
        max_retries=2,
        backoff_seconds=1.0,
        default_headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "Taxi-Intelligence-Platform/0.1.0 (public flight data reader)"
            ),
        },
    ) as http_client:
        collector = SofiaAirportCollector(
            client=SofiaAirportWebsiteClient(
                http_client=http_client,
            ),
            parser=SofiaAirportFlightParser(),
        )

        flights = await collector.collect_arrivals()

    signal = AirportSignalMapper().map_arrivals(
        flights,
        observed_at=datetime.now(SOFIA_TIMEZONE),
    )

    async with AsyncSessionLocal() as session:
        persistence_service = AirportSignalPersistenceService(
            zone_repository=ZoneRepository(session),
            signal_repository=SignalRepository(session),
        )

        stored_signal = await persistence_service.persist(signal)

        print("Stored signal ID:", stored_signal.id)
        print("Signal type:", stored_signal.signal_type)
        print("Source:", stored_signal.source)
        print("Zone ID:", stored_signal.zone_id)
        print("Impact:", stored_signal.impact_score)
        print("Observed at:", stored_signal.observed_at)
        print("Arrivals:", stored_signal.payload["arrivals"])
        print(
            "Flight numbers:",
            stored_signal.payload["flight_numbers"],
        )


if __name__ == "__main__":
    asyncio.run(main())
