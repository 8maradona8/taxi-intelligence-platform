from app.application.handlers import GetCitySnapshotHandler
from app.application.queries import GetCitySnapshotQuery
from app.domain.decision import (
    CityDecisionEngine,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.pipelines import SignalPipeline
from app.services.city_snapshot_service import CitySnapshotService


snapshot_service = CitySnapshotService(
    signal_pipeline=SignalPipeline(),
    city_decision_engine=CityDecisionEngine(),
    opportunity_engine=OpportunityEngine(),
    recommendation_engine=RecommendationEngine(),
)

handler = GetCitySnapshotHandler(
    city_snapshot_service=snapshot_service,
)

query = GetCitySnapshotQuery(
    city_name="Sofia",
)

snapshot = handler.handle(query)

print("City:", snapshot.city_name)
print("Opportunities:", snapshot.opportunity_count)
print("Best recommendation:", snapshot.best_recommendation.summary)

for index, opportunity in enumerate(snapshot.opportunities, start=1):
    print(f"{index}. {opportunity.zone_name} — {opportunity.score}")