from dataclasses import dataclass, field

from app.domain.decision.demand_level import DemandLevel


@dataclass(frozen=True)
class DemandScore:
    score: float
    confidence: float
    level: DemandLevel
    reasons: list[str] = field(default_factory=list)

    @classmethod
    def from_zone_metrics(
        cls,
        *,
        total_impact: float,
        average_confidence: float,
        reasons: list[str],
    ) -> "DemandScore":
        if total_impact < 30:
            level = DemandLevel.LOW
        elif total_impact < 70:
            level = DemandLevel.MEDIUM
        elif total_impact < 120:
            level = DemandLevel.HIGH
        else:
            level = DemandLevel.VERY_HIGH

        return cls(
            score=total_impact,
            confidence=average_confidence,
            level=level,
            reasons=reasons,
        )
