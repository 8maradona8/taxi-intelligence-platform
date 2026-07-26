from app.domain.decision.decision import Decision
from app.domain.decision.decision_action import DecisionAction
from app.domain.decision.decision_reason import DecisionReason
from app.domain.decision.demand_level import DemandLevel
from app.domain.geography import Zone


class DecisionEngine:
    def evaluate_zone(self, zone: Zone) -> Decision:
        demand_score = zone.demand_score()

        reasons = [
            DecisionReason(
                source=signal.source.value,
                description=f"{signal.signal_type.value} contributed {signal.impact_score.value}",
                contribution=signal.impact_score.value,
            )
            for signal in zone.active_signals()
        ]

        if demand_score.level in {DemandLevel.HIGH, DemandLevel.VERY_HIGH}:
            action = DecisionAction.MOVE
        elif demand_score.level == DemandLevel.MEDIUM:
            action = DecisionAction.WAIT
        else:
            action = DecisionAction.AVOID

        return Decision(
            zone=zone,
            demand_score=demand_score,
            action=action,
            reasons=reasons,
        )
