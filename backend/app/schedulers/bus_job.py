from app.core.settings import settings
from app.database.session import AsyncSessionLocal
from app.domain.events import SignalEvent
from app.infrastructure.clients import (
    SofiaCentralBusStationClient,
)
from app.infrastructure.collectors import (
    SofiaCentralBusStationCollector,
)
from app.infrastructure.http import AsyncHttpClient
from app.infrastructure.mappers import (
    BusSignalMapper,
    SofiaCentralBusArrivalParser,
)
from app.repositories import (
    SignalRepository,
    ZoneRepository,
)
from app.services.bus_signal_persistence_service import (
    BusSignalPersistenceService,
)
from app.services.bus_signal_service import BusSignalService


async def collect_and_persist_bus_signal() -> SignalEvent:
    async with AsyncHttpClient(
        base_url="https://www.centralnaavtogara.bg",
        timeout_seconds=20.0,
        max_retries=2,
        backoff_seconds=1.0,
        default_headers={
            "Accept": "text/html,application/xhtml+xml",
            "User-Agent": (
                "Taxi-Intelligence-Platform/0.1.0 (public bus timetable reader)"
            ),
        },
    ) as http_client:
        collector = SofiaCentralBusStationCollector(
            client=SofiaCentralBusStationClient(
                http_client=http_client,
            ),
            parser=SofiaCentralBusArrivalParser(),
            horizon_hours=settings.bus_arrivals_horizon_hours,
        )

        async with AsyncSessionLocal() as session:
            persistence_service = BusSignalPersistenceService(
                zone_repository=ZoneRepository(session),
                signal_repository=SignalRepository(session),
            )

            service = BusSignalService(
                collector=collector,
                signal_mapper=BusSignalMapper(),
                persistence_service=persistence_service,
            )

            return await service.create_arrivals_signal()
