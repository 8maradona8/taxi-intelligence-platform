from dataclasses import asdict

from fastapi import APIRouter

from app.application.dto import CitySnapshotResponse
from app.application.handlers import GetCitySnapshotHandler
from app.application.queries import GetCitySnapshotQuery
from app.domain.decision import (
    CityDecisionEngine,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.pipelines import SignalPipeline
from app.services.city_snapshot_service import CitySnapshotService


router = APIRouter(
    prefix="/cities",
    tags=["City Intelligence"],
)


def build_snapshot_handler() -> GetCitySnapshotHandler:
    snapshot_service = CitySnapshotService(
        signal_pipeline=SignalPipeline(),
        city_decision_engine=CityDecisionEngine(),
        opportunity_engine=OpportunityEngine(),
        recommendation_engine=RecommendationEngine(),
    )

    return GetCitySnapshotHandler(
        city_snapshot_service=snapshot_service,
    )


@router.get("/{city_name}/snapshot")
async def get_city_snapshot(city_name: str):
    handler = build_snapshot_handler()

    snapshot = handler.handle(
        GetCitySnapshotQuery(
            city_name=city_name,
        )
    )

    response = CitySnapshotResponse.from_domain(snapshot)

    return asdict(response)