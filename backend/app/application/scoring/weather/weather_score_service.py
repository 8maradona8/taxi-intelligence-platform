from datetime import timedelta

from app.application.scoring import (
    ScoreEngine,
    ScoreEngineBuilder,
)
from app.application.scoring.weather.context import (
    WEATHER_SNAPSHOT_ATTRIBUTE,
)
from app.application.scoring.weather.precipitation_score_contributor import (
    PrecipitationScoreContributor,
)
from app.application.scoring.weather.temperature_score_contributor import (
    TemperatureScoreContributor,
)
from app.application.scoring.weather.weather_forecast_assessment import (
    WeatherForecastAssessment,
    WeatherForecastWindowAssessment,
)
from app.application.scoring.weather.wind_score_contributor import (
    WindScoreContributor,
)
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContext,
)
from app.domain.weather import (
    WeatherForecast,
    WeatherSnapshot,
)


class WeatherScoreService:
    """Assess weather-related taxi demand pressure."""

    SUBJECT = "weather_demand"

    def __init__(
        self,
        *,
        engine: ScoreEngine | None = None,
    ) -> None:
        self._engine = engine or self._build_default_engine()

    def assess_snapshot(
        self,
        snapshot: WeatherSnapshot,
    ) -> ScoreAssessment:
        """Produce a demand score assessment for a weather snapshot."""
        return self._assess_snapshot(snapshot)

    def assess_forecast_window(
        self,
        snapshot: WeatherSnapshot,
        *,
        window: timedelta,
    ) -> WeatherForecastWindowAssessment:
        """Assess every forecast available inside the supplied window."""
        if window <= timedelta(0):
            raise ValueError("window must be positive")

        relevant_forecasts = snapshot.forecasts_within(window)

        if not relevant_forecasts:
            relevant_forecasts = (snapshot.current_forecast,)

        assessments = tuple(
            self._assess_forecast(
                source_snapshot=snapshot,
                forecast=forecast,
            )
            for forecast in relevant_forecasts
        )

        return WeatherForecastWindowAssessment(
            window=window,
            assessments=assessments,
        )

    def _assess_forecast(
        self,
        *,
        source_snapshot: WeatherSnapshot,
        forecast: WeatherForecast,
    ) -> WeatherForecastAssessment:
        forecast_snapshot = WeatherSnapshot.create(
            location=source_snapshot.location,
            provider=source_snapshot.provider,
            observed_at=forecast.forecast_at,
            forecasts=(forecast,),
        )

        horizon_seconds = (
            forecast.forecast_at - source_snapshot.observed_at
        ).total_seconds()

        return WeatherForecastAssessment(
            forecast_at=forecast.forecast_at,
            horizon_minutes=max(
                0,
                int(horizon_seconds / 60),
            ),
            assessment=self._assess_snapshot(
                forecast_snapshot,
            ),
        )

    def _assess_snapshot(
        self,
        snapshot: WeatherSnapshot,
    ) -> ScoreAssessment:
        context = ScoreContext(
            subject=self.SUBJECT,
            observed_at=snapshot.observed_at,
            attributes={
                WEATHER_SNAPSHOT_ATTRIBUTE: snapshot,
            },
            metadata={
                "location": snapshot.location,
                "provider": snapshot.provider,
                "forecast_count": snapshot.forecast_count,
            },
        )

        return self._engine.assess(context)

    @staticmethod
    def _build_default_engine() -> ScoreEngine:
        return (
            ScoreEngineBuilder()
            .add_many(
                (
                    PrecipitationScoreContributor(),
                    WindScoreContributor(),
                    TemperatureScoreContributor(),
                )
            )
            .build()
        )
