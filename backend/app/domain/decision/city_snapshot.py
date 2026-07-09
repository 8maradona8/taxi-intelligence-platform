from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.decision.opportunity import Opportunity
from app.domain.decision.recommendation import Recommendation


@dataclass(frozen=True)
class CitySnapshot:
    city_name: str
    opportunities: list[Opportunity]
    best_recommendation: Recommendation | None
    generated_at: datetime

    @classmethod
    def create(
        cls,
        *,
        city_name: str,
        opportunities: list[Opportunity],
        best_recommendation: Recommendation | None,
    ) -> "CitySnapshot":
        return cls(
            city_name=city_name,
            opportunities=opportunities,
            best_recommendation=best_recommendation,
            generated_at=datetime.now(UTC),
        )

    @property
    def opportunity_count(self) -> int:
        return len(self.opportunities)

    @property
    def has_recommendation(self) -> bool:
        return self.best_recommendation is not None