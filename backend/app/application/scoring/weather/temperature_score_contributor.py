from app.application.scoring.weather.context import (
    require_weather_snapshot,
)
from app.domain.scoring import (
    ScoreContext,
    ScoreContribution,
    ScoreReason,
)


class TemperatureScoreContributor:
    """Score temperature-related taxi demand pressure."""

    NAME = "weather_temperature"
    DEFAULT_WEIGHT = 0.30
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
        temperature = forecast.air_temperature_celsius

        score, reason_code, description = self._score_temperature(
            temperature,
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
                    "air_temperature_celsius": temperature,
                },
            ),
            metadata={
                "location": snapshot.location,
                "provider": snapshot.provider,
                "forecast_at": forecast.forecast_at.isoformat(),
                "air_temperature_celsius": temperature,
            },
        )

    @staticmethod
    def _score_temperature(
        temperature_celsius: float,
    ) -> tuple[float, str, str]:
        if temperature_celsius < -10.0:
            return (
                90.0,
                "weather_extreme_cold",
                "Extreme cold creates very high taxi demand pressure",
            )

        if temperature_celsius < 0.0:
            return (
                75.0,
                "weather_severe_cold",
                "Severe cold significantly increases expected taxi demand",
            )

        if temperature_celsius < 5.0:
            return (
                55.0,
                "weather_cold",
                "Cold weather increases expected taxi demand",
            )

        if temperature_celsius <= 28.0:
            return (
                10.0,
                "weather_comfortable_temperature",
                ("Comfortable temperature produces limited weather demand pressure"),
            )

        if temperature_celsius <= 33.0:
            return (
                45.0,
                "weather_hot",
                "Hot weather moderately increases expected taxi demand",
            )

        if temperature_celsius <= 38.0:
            return (
                70.0,
                "weather_very_hot",
                "Very hot weather significantly increases taxi demand",
            )

        return (
            90.0,
            "weather_extreme_heat",
            "Extreme heat creates very high taxi demand pressure",
        )

    def _validate_configuration(self) -> None:
        if self._weight <= 0.0:
            raise ValueError("weight must be greater than 0.0")

        if not 0.0 <= self._confidence <= 1.0:
            raise ValueError("confidence must be between 0.0 and 1.0")
