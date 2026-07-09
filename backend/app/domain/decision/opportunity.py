from dataclasses import dataclass

from app.domain.decision.decision import Decision


@dataclass(frozen=True)
class Opportunity:
    decision: Decision
    score: float

    @property
    def zone_name(self) -> str:
        return self.decision.zone.name

    @property
    def action(self):
        return self.decision.action

    @property
    def demand_level(self):
        return self.decision.demand_score.level

    @property
    def confidence(self) -> float:
        return self.decision.confidence