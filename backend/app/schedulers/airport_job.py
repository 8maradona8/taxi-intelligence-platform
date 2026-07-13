from app.database.session import AsyncSessionLocal
from app.domain.events import SignalEvent
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
from app.services.airport_signal_service import AirportSignalService


async def collect_and_persist_airport_signal() -> SignalEvent:
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

        async with AsyncSessionLocal() as session:
            persistence_service = AirportSignalPersistenceService(
                zone_repository=ZoneRepository(session),
                signal_repository=SignalRepository(session),
            )

            service = AirportSignalService(
                collector=collector,
                signal_mapper=AirportSignalMapper(),
                persistence_service=persistence_service,
            )

            return await service.create_arrivals_signal()
