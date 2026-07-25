from app.application.scoring.weather.context import (
    require_weather_snapshot,
)
from app.domain.scoring import (
    ScoreContext,
    ScoreContribution,
    ScoreReason,
)
from app.domain.weather import (
    PrecipitationType,
    WeatherCondition,
    WeatherForecast,
)


class PrecipitationScoreContributor:
    """Score precipitation-related taxi demand pressure."""

    NAME = "weather_precipitation"
    DEFAULT_WEIGHT = 0.50
    DEFAULT_CONFIDENCE = 0.95

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

        score, reason_code, description = self._score_forecast(
            forecast,
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
                    "precipitation_amount_mm": (forecast.precipitation_amount_mm),
                    "precipitation_type": (forecast.precipitation_type.value),
                    "condition": forecast.condition.value,
                },
            ),
            metadata={
                "location": snapshot.location,
                "provider": snapshot.provider,
                "forecast_at": forecast.forecast_at.isoformat(),
                "precipitation_amount_mm": (forecast.precipitation_amount_mm),
                "precipitation_type": (forecast.precipitation_type.value),
            },
        )

    @classmethod
    def _score_forecast(
        cls,
        forecast: WeatherForecast,
    ) -> tuple[float, str, str]:
        amount = forecast.precipitation_amount_mm
        precipitation_type = forecast.precipitation_type
        condition = forecast.condition

        if condition == WeatherCondition.THUNDERSTORM:
            return (
                95.0,
                "weather_thunderstorm",
                "Thunderstorm strongly increases expected taxi demand",
            )

        if precipitation_type in {
            PrecipitationType.SLEET,
            PrecipitationType.MIXED,
        }:
            return (
                max(
                    90.0,
                    cls._score_amount(amount),
                ),
                "weather_sleet_or_mixed_precipitation",
                (
                    "Sleet or mixed precipitation strongly increases "
                    "expected taxi demand"
                ),
            )

        if precipitation_type == PrecipitationType.SNOW:
            return (
                max(
                    85.0,
                    cls._score_amount(amount),
                ),
                "weather_snow",
                "Snow strongly increases expected taxi demand",
            )

        score = cls._score_amount(amount)

        if amount <= 0.0:
            return (
                score,
                "weather_no_precipitation",
                "No precipitation produces limited weather demand pressure",
            )

        if amount <= 0.5:
            return (
                score,
                "weather_light_precipitation",
                "Light precipitation moderately increases expected taxi demand",
            )

        if amount <= 2.0:
            return (
                score,
                "weather_moderate_precipitation",
                "Moderate precipitation increases expected taxi demand",
            )

        if amount <= 5.0:
            return (
                score,
                "weather_heavy_precipitation",
                "Heavy precipitation strongly increases expected taxi demand",
            )

        return (
            score,
            "weather_extreme_precipitation",
            "Extreme precipitation creates very high taxi demand pressure",
        )

    @staticmethod
    def _score_amount(
        amount: float,
    ) -> float:
        if amount <= 0.0:
            return 10.0

        if amount <= 0.5:
            return 35.0

        if amount <= 2.0:
            return 60.0

        if amount <= 5.0:
            return 80.0

        return 95.0

    def _validate_configuration(self) -> None:
        if self._weight <= 0.0:
            raise ValueError("weight must be greater than 0.0")

        if not 0.0 <= self._confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
