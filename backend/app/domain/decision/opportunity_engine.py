from app.domain.decision.decision import Decision
from app.domain.decision.opportunity import Opportunity


class OpportunityEngine:
    def calculate(self, decision: Decision) -> Opportunity:
        demand_score = decision.demand_score.score
        confidence_bonus = decision.confidence * 20
        reason_bonus = len(decision.reasons) * 5

        score = demand_score + confidence_bonus + reason_bonus

        return Opportunity(
            decision=decision,
            score=round(score, 2),
        )

    def rank(self, decisions: list[Decision]) -> list[Opportunity]:
        opportunities = [
            self.calculate(decision)
            for decision in decisions
        ]

        return sorted(
            opportunities,
            key=lambda opportunity: opportunity.score,
            reverse=True,
        )