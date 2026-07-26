from dataclasses import dataclass
from datetime import datetime, timedelta

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


@dataclass(frozen=True, slots=True)
class WeatherForecastWindowAssessment:
    """Collection of weather assessments inside one forecast window."""

    window: timedelta
    assessments: tuple[WeatherForecastAssessment, ...]

    def __post_init__(self) -> None:
        if self.window <= timedelta(0):
            raise ValueError("window must be positive")

        if not self.assessments:
            raise ValueError("assessments cannot be empty")

        forecast_times = tuple(
            assessment.forecast_at for assessment in self.assessments
        )

        if len(forecast_times) != len(set(forecast_times)):
            raise ValueError("assessments cannot contain duplicate forecast_at values")

        if forecast_times != tuple(sorted(forecast_times)):
            raise ValueError("assessments must be ordered by forecast_at")

    @property
    def window_minutes(self) -> int:
        return int(self.window.total_seconds() / 60)

    @property
    def forecast_count(self) -> int:
        return len(self.assessments)

    @property
    def peak(self) -> WeatherForecastAssessment:
        """Return the earliest assessment with the highest score."""
        return max(
            self.assessments,
            key=lambda item: item.assessment.score,
        )
