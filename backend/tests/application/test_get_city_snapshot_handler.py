import pytest

from app.application.handlers import GetCitySnapshotHandler
from app.application.queries import GetCitySnapshotQuery
from app.domain.decision import (
    CityDecisionEngine,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.events import SignalEvent
from app.domain.pipelines import SignalPipeline
from app.services.city_snapshot_service import CitySnapshotService


class EmptyAirportSignalReader:
    async def get_latest_active_signal(
        self,
    ) -> SignalEvent | None:
        return None


@pytest.mark.anyio
async def test_handler_returns_sofia_snapshot(
    snapshot_handler: GetCitySnapshotHandler,
) -> None:
    query = GetCitySnapshotQuery(
        city_name="Sofia",
    )

    snapshot = await snapshot_handler.handle(query)

    assert snapshot.city_name == "Sofia"
    assert snapshot.opportunity_count == 2
    assert snapshot.has_recommendation is True

    recommendation = snapshot.best_recommendation

    assert recommendation is not None
    assert recommendation.zone_name == "Sofia Airport"
    assert recommendation.summary == "MOVE to Sofia Airport"

    assert snapshot.opportunities[0].zone_name == "Sofia Airport"
    assert snapshot.opportunities[1].zone_name == "NDK"


@pytest.mark.anyio
async def test_handler_works_without_active_airport_signal() -> None:
    handler = GetCitySnapshotHandler(
        city_snapshot_service=CitySnapshotService(
            signal_pipeline=SignalPipeline(),
            city_decision_engine=CityDecisionEngine(),
            opportunity_engine=OpportunityEngine(),
            recommendation_engine=RecommendationEngine(),
        ),
        airport_signal_reader=EmptyAirportSignalReader(),
    )

    snapshot = await handler.handle(
        GetCitySnapshotQuery(
            city_name="Sofia",
        )
    )

    assert snapshot.city_name == "Sofia"
    assert snapshot.opportunity_count == 2
    assert snapshot.best_recommendation is not None
    assert snapshot.best_recommendation.zone_name == "NDK"
