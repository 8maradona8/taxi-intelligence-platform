from app.domain.decision import (
    CityDecisionEngine,
    CitySnapshot,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.events import SignalEvent
from app.domain.geography import City
from app.domain.pipelines import SignalPipeline


class CitySnapshotService:
    def __init__(self) -> None:
        self.signal_pipeline = SignalPipeline()
        self.city_decision_engine = CityDecisionEngine()
        self.opportunity_engine = OpportunityEngine()
        self.recommendation_engine = RecommendationEngine()

    def create_snapshot(
        self,
        *,
        city: City,
        signals: list[SignalEvent],
    ) -> CitySnapshot:
        self.signal_pipeline.process_city(
            city=city,
            signals=signals,
        )

        decisions = self.city_decision_engine.evaluate_city(city)
        opportunities = self.opportunity_engine.rank(decisions)
        best_recommendation = self.recommendation_engine.recommend_best(
            opportunities
        )

        return CitySnapshot.create(
            city_name=city.name,
            opportunities=opportunities,
            best_recommendation=best_recommendation,
        )