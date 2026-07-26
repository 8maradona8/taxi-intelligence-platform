from datetime import UTC, datetime, timedelta

from app.domain.decision.opportunity import Opportunity
from app.domain.decision.recommendation import Recommendation
from app.domain.decision.recommendation_urgency import RecommendationUrgency


class RecommendationEngine:
    def recommend_best(
        self,
        opportunities: list[Opportunity],
    ) -> Recommendation | None:
        if not opportunities:
            return None

        best_opportunity = opportunities[0]

        urgency = self._calculate_urgency(best_opportunity.score)

        return Recommendation(
            title=f"Move to {best_opportunity.zone_name}",
            zone_name=best_opportunity.zone_name,
            action=best_opportunity.action,
            urgency=urgency,
            demand_level=best_opportunity.demand_level,
            confidence=best_opportunity.confidence,
            reasons=best_opportunity.decision.reasons,
            valid_until=datetime.now(UTC) + timedelta(minutes=45),
        )

    def _calculate_urgency(
        self,
        score: float,
    ) -> RecommendationUrgency:
        if score >= 150:
            return RecommendationUrgency.CRITICAL

        if score >= 100:
            return RecommendationUrgency.HIGH

        if score >= 60:
            return RecommendationUrgency.MEDIUM

        return RecommendationUrgency.LOW
