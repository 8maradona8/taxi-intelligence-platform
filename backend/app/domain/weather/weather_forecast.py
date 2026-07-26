from dataclasses import dataclass
from datetime import datetime

from app.domain.weather.precipitation_type import (
    PrecipitationType,
)
from app.domain.weather.weather_condition import (
    WeatherCondition,
)


@dataclass(frozen=True, slots=True)
class WeatherForecast:
    forecast_at: datetime
    air_temperature_celsius: float
    relative_humidity_percent: float
    wind_speed_mps: float
    wind_from_direction_degrees: float
    cloud_area_fraction_percent: float
    air_pressure_at_sea_level_hpa: float
    precipitation_amount_mm: float
    symbol_code: str

    def __post_init__(self) -> None:
        if self.forecast_at.tzinfo is None:
            raise ValueError("forecast_at must be timezone-aware")

        if not (-100.0 <= self.air_temperature_celsius <= 70.0):
            raise ValueError("air_temperature_celsius must be between -100 and 70")

        if not (0.0 <= self.relative_humidity_percent <= 100.0):
            raise ValueError("relative_humidity_percent must be between 0 and 100")

        if self.wind_speed_mps < 0.0:
            raise ValueError("wind_speed_mps cannot be negative")

        if not (0.0 <= self.wind_from_direction_degrees <= 360.0):
            raise ValueError("wind_from_direction_degrees must be between 0 and 360")

        if not (0.0 <= self.cloud_area_fraction_percent <= 100.0):
            raise ValueError("cloud_area_fraction_percent must be between 0 and 100")

        if self.air_pressure_at_sea_level_hpa <= 0.0:
            raise ValueError("air_pressure_at_sea_level_hpa must be greater than zero")

        if self.precipitation_amount_mm < 0.0:
            raise ValueError("precipitation_amount_mm cannot be negative")

        normalized_symbol_code = self.symbol_code.strip().lower()

        if not normalized_symbol_code:
            raise ValueError("symbol_code cannot be empty")

        object.__setattr__(
            self,
            "symbol_code",
            normalized_symbol_code,
        )

    @property
    def condition(self) -> WeatherCondition:
        return WeatherCondition.from_symbol_code(self.symbol_code)

    @property
    def precipitation_type(
        self,
    ) -> PrecipitationType:
        return PrecipitationType.from_symbol_code(
            self.symbol_code,
            precipitation_amount_mm=(self.precipitation_amount_mm),
        )

    @property
    def has_precipitation(self) -> bool:
        return self.precipitation_amount_mm > 0.0
