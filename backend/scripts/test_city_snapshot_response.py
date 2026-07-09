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


snapshot_service = CitySnapshotService(
    signal_pipeline=SignalPipeline(),
    city_decision_engine=CityDecisionEngine(),
    opportunity_engine=OpportunityEngine(),
    recommendation_engine=RecommendationEngine(),
)

handler = GetCitySnapshotHandler(
    city_snapshot_service=snapshot_service,
)

snapshot = handler.handle(
    GetCitySnapshotQuery(
        city_name="Sofia",
    )
)

response = CitySnapshotResponse.from_domain(snapshot)

print("City:", response.city_name)
print("Generated at:", response.generated_at)
print("Opportunities:", len(response.opportunities))

if response.best_recommendation:
    print("Best:", response.best_recommendation.summary)
    print("Urgency:", response.best_recommendation.urgency)
    print("Confidence:", response.best_recommendation.confidence)

for opportunity in response.opportunities:
    print(
        f"{opportunity.rank}. {opportunity.zone_name} "
        f"{opportunity.score} {opportunity.demand_level}"
    )