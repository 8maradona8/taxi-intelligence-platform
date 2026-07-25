from app.application.scoring.weather.context import (
    require_weather_snapshot,
)
from app.domain.scoring import (
    ScoreContext,
    ScoreContribution,
    ScoreReason,
)


class WindScoreContributor:
    """Score wind-related taxi demand pressure."""

    NAME = "weather_wind"
    DEFAULT_WEIGHT = 0.20
    DEFAULT_CONFIDENCE = 0.90

    def __init__(
        self,
        *,
        weight: float = DEFAULT_WEIGHT,
        confidence: float = DEFAULT_CONFIDENCE,
    ) -> None:
        self._weight = weight
        self._confidence = confidence

        self._validate_configuration()

    @property
    def name(self) -> str:
        return self.NAME

    def evaluate(
        self,
        context: ScoreContext,
    ) -> ScoreContribution:
        snapshot = require_weather_snapshot(context)
        forecast = snapshot.current_forecast
        wind_speed = forecast.wind_speed_mps

        score, reason_code, description = self._score_wind(
            wind_speed,
        )

        return ScoreContribution(
            contributor=self.name,
            score=score,
            weight=self._weight,
            confidence=self._confidence,
            reason=ScoreReason(
                code=reason_code,
                description=description,
                contribution=score,
                metadata={
                    "wind_speed_mps": wind_speed,
                    "wind_from_direction_degrees": (
                        forecast.wind_from_direction_degrees
                    ),
                },
            ),
            metadata={
                "location": snapshot.location,
                "provider": snapshot.provider,
                "forecast_at": forecast.forecast_at.isoformat(),
                "wind_speed_mps": wind_speed,
            },
        )

    @staticmethod
    def _score_wind(
        wind_speed_mps: float,
    ) -> tuple[float, str, str]:
        if wind_speed_mps < 3.0:
            return (
                10.0,
                "weather_calm_wind",
                "Calm wind produces limited weather demand pressure",
            )

        if wind_speed_mps < 6.0:
            return (
                25.0,
                "weather_light_wind",
                "Light wind slightly increases expected taxi demand",
            )

        if wind_speed_mps < 10.0:
            return (
                50.0,
                "weather_strong_wind",
                "Strong wind increases expected taxi demand",
            )

        if wind_speed_mps < 15.0:
            return (
                75.0,
                "weather_very_strong_wind",
                "Very strong wind significantly increases taxi demand",
            )

        return (
            90.0,
            "weather_extreme_wind",
            "Extreme wind creates very high taxi demand pressure",
        )

    def _validate_configuration(self) -> None:
        if self._weight <= 0.0:
            raise ValueError("weight must be greater than 0.0")

        if not 0.0 <= self._confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
