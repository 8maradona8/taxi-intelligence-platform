from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.domain.weather.weather_forecast import (
    WeatherForecast,
)


@dataclass(frozen=True, slots=True)
class WeatherSnapshot:
    location: str
    provider: str
    observed_at: datetime
    forecasts: tuple[WeatherForecast, ...]

    def __post_init__(self) -> None:
        normalized_location = self.location.strip()
        normalized_provider = self.provider.strip().lower()

        if not normalized_location:
            raise ValueError("location cannot be empty")

        if not normalized_provider:
            raise ValueError("provider cannot be empty")

        normalized_observed_at = self._normalize_datetime(self.observed_at)
        ordered_forecasts = tuple(
            sorted(
                self.forecasts,
                key=lambda forecast: forecast.forecast_at,
            )
        )

        if not ordered_forecasts:
            raise ValueError("forecasts cannot be empty")

        forecast_times = [forecast.forecast_at for forecast in ordered_forecasts]

        if len(forecast_times) != len(set(forecast_times)):
            raise ValueError("forecasts cannot contain duplicate forecast_at values")

        object.__setattr__(
            self,
            "location",
            normalized_location,
        )
        object.__setattr__(
            self,
            "provider",
            normalized_provider,
        )
        object.__setattr__(
            self,
            "observed_at",
            normalized_observed_at,
        )
        object.__setattr__(
            self,
            "forecasts",
            ordered_forecasts,
        )

    @classmethod
    def create(
        cls,
        *,
        forecasts: Sequence[WeatherForecast],
        observed_at: datetime,
        location: str = "Sofia",
        provider: str = "met-norway",
    ) -> "WeatherSnapshot":
        return cls(
            location=location,
            provider=provider,
            observed_at=observed_at,
            forecasts=tuple(forecasts),
        )

    @property
    def current_forecast(self) -> WeatherForecast:
        for forecast in self.forecasts:
            if forecast.forecast_at >= self.observed_at:
                return forecast

        return self.forecasts[-1]

    @property
    def forecast_count(self) -> int:
        return len(self.forecasts)

    def forecasts_within(
        self,
        window: timedelta,
    ) -> tuple[WeatherForecast, ...]:
        if window <= timedelta(0):
            raise ValueError("window must be positive")

        window_end = self.observed_at + window

        return tuple(
            forecast
            for forecast in self.forecasts
            if self.observed_at <= forecast.forecast_at <= window_end
        )

    @staticmethod
    def _normalize_datetime(
        value: datetime,
    ) -> datetime:
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)

        return value.astimezone(UTC)
