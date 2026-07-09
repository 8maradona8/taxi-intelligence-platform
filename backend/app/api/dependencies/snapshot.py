from app.application.handlers import GetCitySnapshotHandler
from app.domain.decision import (
    CityDecisionEngine,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.pipelines import SignalPipeline
from app.services.city_snapshot_service import CitySnapshotService


def get_snapshot_handler() -> GetCitySnapshotHandler:
    snapshot_service = CitySnapshotService(
        signal_pipeline=SignalPipeline(),
        city_decision_engine=CityDecisionEngine(),
        opportunity_engine=OpportunityEngine(),
        recommendation_engine=RecommendationEngine(),
    )

    return GetCitySnapshotHandler(
        city_snapshot_service=snapshot_service,
    )