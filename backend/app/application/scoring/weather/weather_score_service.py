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
from app.application.scoring.weather.wind_score_contributor import (
    WindScoreContributor,
)
from app.domain.scoring import (
    ScoreAssessment,
    ScoreContext,
)
from app.domain.weather import WeatherSnapshot


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
