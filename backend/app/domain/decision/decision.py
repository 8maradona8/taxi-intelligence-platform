from dataclasses import dataclass

from app.domain.decision.decision_action import DecisionAction
from app.domain.decision.demand_score import DemandScore
from app.domain.geography import Zone
from app.domain.decision.decision_reason import DecisionReason


@dataclass(frozen=True)
class Decision:
    zone: Zone
    demand_score: DemandScore
    action: DecisionAction
    reasons: list[DecisionReason]

    @property
    def confidence(self) -> float:
        return self.demand_score.confidence