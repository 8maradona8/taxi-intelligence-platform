from dataclasses import dataclass
from datetime import datetime

from app.domain.scoring import ScoreAssessment


@dataclass(frozen=True, slots=True)
class WeatherForecastAssessment:
    """Score assessment associated with one weather forecast horizon."""

    forecast_at: datetime
    horizon_minutes: int
    assessment: ScoreAssessment

    def __post_init__(self) -> None:
        if self.forecast_at.tzinfo is None:
            raise ValueError("forecast_at must be timezone-aware")

        if self.horizon_minutes < 0:
            raise ValueError("horizon_minutes cannot be negative")
