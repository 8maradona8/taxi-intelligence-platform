from dataclasses import dataclass
from datetime import datetime

from app.domain.decision import CitySnapshot


@dataclass(frozen=True)
class OpportunityResponse:
    rank: int
    zone_name: str
    action: str
    demand_level: str
    confidence: int
    score: float


@dataclass(frozen=True)
class RecommendationResponse:
    title: str
    summary: str
    zone_name: str
    action: str
    urgency: str
    demand_level: str
    confidence: int
    reasons: int
    valid_until: datetime


@dataclass(frozen=True)
class CitySnapshotResponse:
    city_name: str
    generated_at: datetime
    opportunities: list[OpportunityResponse]
    best_recommendation: RecommendationResponse | None

    @classmethod
    def from_domain(
        cls,
        snapshot: CitySnapshot,
    ) -> "CitySnapshotResponse":
        opportunities = [
            OpportunityResponse(
                rank=index,
                zone_name=opportunity.zone_name,
                action=opportunity.action.value,
                demand_level=opportunity.demand_level.value,
                confidence=round(opportunity.confidence * 100),
                score=opportunity.score,
            )
            for index, opportunity in enumerate(
                snapshot.opportunities,
                start=1,
            )
        ]

        best_recommendation = None

        if snapshot.best_recommendation is not None:
            recommendation = snapshot.best_recommendation

            best_recommendation = RecommendationResponse(
                title=recommendation.title,
                summary=recommendation.summary,
                zone_name=recommendation.zone_name,
                action=recommendation.action.value,
                urgency=recommendation.urgency.value,
                demand_level=recommendation.demand_level.value,
                confidence=recommendation.confidence_percent,
                reasons=recommendation.reason_count,
                valid_until=recommendation.valid_until,
            )

        return cls(
            city_name=snapshot.city_name,
            generated_at=snapshot.generated_at,
            opportunities=opportunities,
            best_recommendation=best_recommendation,
        )
