from datetime import UTC, datetime, timedelta
from typing import Any

from app.application.scoring.weather import (
    WeatherForecastWindowAssessment,
    WeatherScoreService,
)
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.scoring import (
    ScoreAssessment,
    ScoreLevel,
)
from app.domain.value_objects import (
    Confidence,
    ImpactScore,
)
from app.domain.weather import (
    WeatherForecast,
    WeatherSnapshot,
)


class WeatherSignalMapper:
    RAW_SCORING_VERSION = "raw-weather-v1"
    DEMAND_SCORING_VERSION = "weather-demand-v1"
    FORECAST_SCORING_VERSION = "weather-forecast-window-v1"

    def __init__(
        self,
        *,
        zone_name: str = "Sofia",
        forecast_window: timedelta = timedelta(hours=6),
        signal_ttl: timedelta = timedelta(minutes=30),
        score_service: WeatherScoreService | None = None,
    ) -> None:
        normalized_zone_name = zone_name.strip()

        if not normalized_zone_name:
            raise ValueError("zone_name cannot be empty")

        if forecast_window <= timedelta(0):
            raise ValueError("forecast_window must be positive")

        if signal_ttl <= timedelta(0):
            raise ValueError("signal_ttl must be positive")

        self._zone_name = normalized_zone_name
        self._forecast_window = forecast_window
        self._signal_ttl = signal_ttl
        self._score_service = score_service

    def map_forecasts(
        self,
        forecasts: list[WeatherForecast],
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        snapshot = WeatherSnapshot.create(
            location=self._zone_name,
            provider="met-norway",
            observed_at=observed_at or datetime.now(UTC),
            forecasts=forecasts,
        )

        current_forecast = snapshot.current_forecast
        relevant_forecasts = snapshot.forecasts_within(
            self._forecast_window,
        )

        if not relevant_forecasts:
            relevant_forecasts = (current_forecast,)

        base_payload: dict[str, Any] = {
            "provider": snapshot.provider,
            "location": snapshot.location,
            "arrivals": 0,
            "forecast_window_minutes": int(self._forecast_window.total_seconds() / 60),
            "forecast_count": len(relevant_forecasts),
            "current": self._serialize_forecast(
                current_forecast,
            ),
            "forecasts": [
                self._serialize_forecast(forecast) for forecast in relevant_forecasts
            ],
        }

        if self._score_service is None:
            return self._create_raw_signal(
                snapshot=snapshot,
                payload=base_payload,
            )

        window_assessment = self._score_service.assess_forecast_window(
            snapshot,
            window=self._forecast_window,
        )
        peak_assessment = window_assessment.peak.assessment

        return self._create_scored_signal(
            snapshot=snapshot,
            assessment=peak_assessment,
            window_assessment=window_assessment,
            payload=base_payload,
        )

    def _create_raw_signal(
        self,
        *,
        snapshot: WeatherSnapshot,
        payload: dict[str, Any],
    ) -> SignalEvent:
        return SignalEvent(
            source=SignalSource.WEATHER,
            signal_type=SignalType.WEATHER_CONDITION,
            zone_name=snapshot.location,
            impact_score=ImpactScore(0.0),
            confidence=Confidence(0.95),
            priority=PriorityLevel.LOW,
            observed_at=snapshot.observed_at,
            ttl=self._signal_ttl,
            payload={
                **payload,
                "demand_impact_scored": False,
                "scoring_version": self.RAW_SCORING_VERSION,
            },
        )

    def _create_scored_signal(
        self,
        *,
        snapshot: WeatherSnapshot,
        assessment: ScoreAssessment,
        window_assessment: WeatherForecastWindowAssessment,
        payload: dict[str, Any],
    ) -> SignalEvent:
        return SignalEvent(
            source=SignalSource.WEATHER,
            signal_type=SignalType.WEATHER_CONDITION,
            zone_name=snapshot.location,
            impact_score=ImpactScore(
                assessment.score,
            ),
            confidence=Confidence(
                assessment.confidence,
            ),
            priority=self._priority_from_level(
                assessment.level,
            ),
            observed_at=snapshot.observed_at,
            ttl=self._signal_ttl,
            payload={
                **payload,
                "demand_impact_scored": True,
                "scoring_version": self.DEMAND_SCORING_VERSION,
                "scoring": self._serialize_assessment(
                    assessment,
                ),
                "forecast_scoring": (
                    self._serialize_window_assessment(
                        window_assessment,
                    )
                ),
            },
        )

    @staticmethod
    def _priority_from_level(
        level: ScoreLevel,
    ) -> PriorityLevel:
        priority_by_level = {
            ScoreLevel.VERY_LOW: PriorityLevel.LOW,
            ScoreLevel.LOW: PriorityLevel.LOW,
            ScoreLevel.MEDIUM: PriorityLevel.MEDIUM,
            ScoreLevel.HIGH: PriorityLevel.HIGH,
            ScoreLevel.VERY_HIGH: PriorityLevel.CRITICAL,
        }

        return priority_by_level[level]

    @classmethod
    def _serialize_window_assessment(
        cls,
        window_assessment: WeatherForecastWindowAssessment,
    ) -> dict[str, Any]:
        peak = window_assessment.peak

        return {
            "scoring_version": cls.FORECAST_SCORING_VERSION,
            "window_minutes": window_assessment.window_minutes,
            "forecast_count": window_assessment.forecast_count,
            "peak_score": peak.assessment.score,
            "peak_forecast_at": peak.forecast_at.isoformat(),
            "assessments": [
                {
                    "forecast_at": item.forecast_at.isoformat(),
                    "horizon_minutes": item.horizon_minutes,
                    **cls._serialize_assessment(
                        item.assessment,
                    ),
                }
                for item in window_assessment.assessments
            ],
        }

    @staticmethod
    def _serialize_assessment(
        assessment: ScoreAssessment,
    ) -> dict[str, Any]:
        return {
            "score": assessment.score,
            "confidence": assessment.confidence,
            "level": assessment.level.value,
            "contributors": [
                {
                    "name": contribution.contributor,
                    "score": contribution.score,
                    "weight": contribution.weight,
                    "confidence": contribution.confidence,
                    "weighted_score": contribution.weighted_score,
                    "reason_code": contribution.reason.code,
                }
                for contribution in assessment.contributions
            ],
            "reasons": [
                {
                    "code": reason.code,
                    "description": reason.description,
                    "contribution": reason.contribution,
                    "metadata": dict(reason.metadata),
                }
                for reason in assessment.reasons
            ],
            "metadata": dict(assessment.metadata),
        }

    @staticmethod
    def _serialize_forecast(
        forecast: WeatherForecast,
    ) -> dict[str, object]:
        return {
            "forecast_at": forecast.forecast_at.isoformat(),
            "air_temperature_celsius": (forecast.air_temperature_celsius),
            "relative_humidity_percent": (forecast.relative_humidity_percent),
            "wind_speed_mps": forecast.wind_speed_mps,
            "wind_from_direction_degrees": (forecast.wind_from_direction_degrees),
            "cloud_area_fraction_percent": (forecast.cloud_area_fraction_percent),
            "air_pressure_at_sea_level_hpa": (forecast.air_pressure_at_sea_level_hpa),
            "precipitation_amount_mm": (forecast.precipitation_amount_mm),
            "symbol_code": forecast.symbol_code,
        }
