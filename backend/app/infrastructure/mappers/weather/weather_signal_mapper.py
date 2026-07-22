from datetime import UTC, datetime, timedelta

from app.domain import WeatherForecast
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import (
    Confidence,
    ImpactScore,
)


class WeatherSignalMapper:
    def __init__(
        self,
        *,
        zone_name: str = "Sofia",
        forecast_window: timedelta = timedelta(hours=6),
        signal_ttl: timedelta = timedelta(minutes=30),
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

    def map_forecasts(
        self,
        forecasts: list[WeatherForecast],
        *,
        observed_at: datetime | None = None,
    ) -> SignalEvent:
        if not forecasts:
            raise ValueError("forecasts cannot be empty")

        observation_time = self._normalize_observed_at(observed_at or datetime.now(UTC))

        ordered_forecasts = sorted(
            forecasts,
            key=lambda forecast: forecast.forecast_at,
        )

        current_forecast = self._select_current_forecast(
            ordered_forecasts,
            observed_at=observation_time,
        )

        relevant_forecasts = self._select_relevant_forecasts(
            ordered_forecasts,
            observed_at=observation_time,
        )

        if not relevant_forecasts:
            relevant_forecasts = [current_forecast]

        return SignalEvent(
            source=SignalSource.WEATHER,
            signal_type=SignalType.WEATHER_CONDITION,
            zone_name=self._zone_name,
            impact_score=ImpactScore(0.0),
            confidence=Confidence(0.95),
            priority=PriorityLevel.LOW,
            observed_at=observation_time,
            ttl=self._signal_ttl,
            payload={
                "provider": "met-norway",
                "location": self._zone_name,
                "arrivals": 0,
                "demand_impact_scored": False,
                "scoring_version": "raw-weather-v1",
                "forecast_window_minutes": int(
                    self._forecast_window.total_seconds() / 60
                ),
                "forecast_count": len(relevant_forecasts),
                "current": self._serialize_forecast(
                    current_forecast,
                ),
                "forecasts": [
                    self._serialize_forecast(forecast)
                    for forecast in relevant_forecasts
                ],
            },
        )

    def _select_current_forecast(
        self,
        forecasts: list[WeatherForecast],
        *,
        observed_at: datetime,
    ) -> WeatherForecast:
        future_forecasts = [
            forecast for forecast in forecasts if forecast.forecast_at >= observed_at
        ]

        if future_forecasts:
            return future_forecasts[0]

        return forecasts[-1]

    def _select_relevant_forecasts(
        self,
        forecasts: list[WeatherForecast],
        *,
        observed_at: datetime,
    ) -> list[WeatherForecast]:
        window_end = observed_at + self._forecast_window

        return [
            forecast
            for forecast in forecasts
            if observed_at <= forecast.forecast_at <= window_end
        ]

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

    @staticmethod
    def _normalize_observed_at(
        observed_at: datetime,
    ) -> datetime:
        if observed_at.tzinfo is None:
            return observed_at.replace(tzinfo=UTC)

        return observed_at.astimezone(UTC)
