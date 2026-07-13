from collections.abc import AsyncIterator

from app.application.handlers import GetCitySnapshotHandler
from app.database.session import AsyncSessionLocal
from app.domain.decision import (
    CityDecisionEngine,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.pipelines import SignalPipeline
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
from app.services.city_snapshot_service import CitySnapshotService


async def get_snapshot_handler() -> AsyncIterator[GetCitySnapshotHandler]:
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
        airport_client = SofiaAirportWebsiteClient(
            http_client=http_client,
        )

        airport_collector = SofiaAirportCollector(
            client=airport_client,
            parser=SofiaAirportFlightParser(),
        )

        async with AsyncSessionLocal() as session:
            persistence_service = AirportSignalPersistenceService(
                zone_repository=ZoneRepository(session),
                signal_repository=SignalRepository(session),
            )

            airport_signal_service = AirportSignalService(
                collector=airport_collector,
                signal_mapper=AirportSignalMapper(),
                persistence_service=persistence_service,
            )

            snapshot_service = CitySnapshotService(
                signal_pipeline=SignalPipeline(),
                city_decision_engine=CityDecisionEngine(),
                opportunity_engine=OpportunityEngine(),
                recommendation_engine=RecommendationEngine(),
            )

            yield GetCitySnapshotHandler(
                city_snapshot_service=snapshot_service,
                airport_signal_service=airport_signal_service,
            )
