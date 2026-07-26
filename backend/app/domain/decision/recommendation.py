from dataclasses import dataclass
from datetime import datetime

from app.domain.decision.decision_action import DecisionAction
from app.domain.decision.decision_reason import DecisionReason
from app.domain.decision.demand_level import DemandLevel
from app.domain.decision.recommendation_urgency import RecommendationUrgency


@dataclass(frozen=True)
class Recommendation:
    title: str
    zone_name: str
    action: DecisionAction
    urgency: RecommendationUrgency
    demand_level: DemandLevel
    confidence: float
    reasons: list[DecisionReason]
    valid_until: datetime

    @property
    def summary(self) -> str:
        return f"{self.action.value.upper()} to {self.zone_name}"

    @property
    def confidence_percent(self) -> int:
        return round(self.confidence * 100)

    @property
    def reason_count(self) -> int:
        return len(self.reasons)
