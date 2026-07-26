from collections.abc import AsyncIterator

from app.application.handlers import GetCitySnapshotHandler
from app.database.session import AsyncSessionLocal
from app.domain.decision import (
    CityDecisionEngine,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.pipelines import SignalPipeline
from app.repositories import SignalRepository, ZoneRepository
from app.services.airport_signal_read_service import (
    AirportSignalReadService,
)
from app.services.city_snapshot_service import CitySnapshotService


async def get_snapshot_handler() -> AsyncIterator[GetCitySnapshotHandler]:
    async with AsyncSessionLocal() as session:
        airport_signal_reader = AirportSignalReadService(
            zone_repository=ZoneRepository(session),
            signal_repository=SignalRepository(session),
        )

        snapshot_service = CitySnapshotService(
            signal_pipeline=SignalPipeline(),
            city_decision_engine=CityDecisionEngine(),
            opportunity_engine=OpportunityEngine(),
            recommendation_engine=RecommendationEngine(),
        )

        yield GetCitySnapshotHandler(
            city_snapshot_service=snapshot_service,
            airport_signal_reader=airport_signal_reader,
        )
