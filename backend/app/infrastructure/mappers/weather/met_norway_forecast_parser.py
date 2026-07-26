from datetime import datetime
from typing import Any

from app.domain import WeatherForecast


class MetNorwayForecastParser:
    PERIOD_PRIORITY = (
        "next_1_hours",
        "next_6_hours",
        "next_12_hours",
    )

    REQUIRED_INSTANT_FIELDS = (
        "air_pressure_at_sea_level",
        "air_temperature",
        "cloud_area_fraction",
        "relative_humidity",
        "wind_from_direction",
        "wind_speed",
    )

    def parse_forecasts(
        self,
        payload: dict[str, Any],
    ) -> list[WeatherForecast]:
        timeseries = self._extract_timeseries(payload)

        forecasts: list[WeatherForecast] = []

        for index, point in enumerate(timeseries):
            try:
                forecast = self._parse_forecast_point(point)
            except (
                KeyError,
                TypeError,
                ValueError,
            ) as exc:
                raise ValueError(
                    f"Invalid MET Norway forecast point at index {index}: {exc}"
                ) from exc

            if forecast is not None:
                forecasts.append(forecast)

        if not forecasts:
            raise ValueError("MET Norway response contains no complete forecast points")

        return forecasts

    @staticmethod
    def _extract_timeseries(
        payload: dict[str, Any],
    ) -> list[dict[str, Any]]:
        if payload.get("type") != "Feature":
            raise ValueError("MET Norway response type must be Feature")

        properties = payload.get("properties")

        if not isinstance(properties, dict):
            raise ValueError("MET Norway response properties must be an object")

        timeseries = properties.get("timeseries")

        if not isinstance(timeseries, list):
            raise ValueError("MET Norway timeseries must be a list")

        if not all(isinstance(point, dict) for point in timeseries):
            raise ValueError("MET Norway timeseries items must be objects")

        return timeseries

    def _parse_forecast_point(
        self,
        point: dict[str, Any],
    ) -> WeatherForecast | None:
        forecast_at = self._parse_datetime(
            self._require_string(
                point,
                "time",
            )
        )

        data = self._require_mapping(
            point,
            "data",
        )

        instant = self._require_mapping(
            data,
            "instant",
        )

        details = self._require_mapping(
            instant,
            "details",
        )

        for field in self.REQUIRED_INSTANT_FIELDS:
            if field not in details:
                raise KeyError(f"missing instant field: {field}")

        period_data = self._extract_period_data(data)

        if period_data is None:
            return None

        precipitation_amount_mm, symbol_code = period_data

        return WeatherForecast(
            forecast_at=forecast_at,
            air_temperature_celsius=self._require_number(
                details,
                "air_temperature",
            ),
            relative_humidity_percent=self._require_number(
                details,
                "relative_humidity",
            ),
            wind_speed_mps=self._require_number(
                details,
                "wind_speed",
            ),
            wind_from_direction_degrees=self._require_number(
                details,
                "wind_from_direction",
            ),
            cloud_area_fraction_percent=self._require_number(
                details,
                "cloud_area_fraction",
            ),
            air_pressure_at_sea_level_hpa=self._require_number(
                details,
                "air_pressure_at_sea_level",
            ),
            precipitation_amount_mm=precipitation_amount_mm,
            symbol_code=symbol_code,
        )

    def _extract_period_data(
        self,
        data: dict[str, Any],
    ) -> tuple[float, str] | None:
        for period_name in self.PERIOD_PRIORITY:
            raw_period = data.get(period_name)

            if raw_period is None:
                continue

            if not isinstance(raw_period, dict):
                raise ValueError(f"{period_name} must be an object")

            summary = raw_period.get("summary")

            if not isinstance(summary, dict):
                raise ValueError(f"{period_name}.summary must be an object")

            symbol_code = summary.get("symbol_code")

            if not isinstance(symbol_code, str):
                raise ValueError(f"{period_name}.summary.symbol_code must be a string")

            normalized_symbol_code = symbol_code.strip()

            if not normalized_symbol_code:
                raise ValueError(f"{period_name}.summary.symbol_code cannot be empty")

            raw_details = raw_period.get(
                "details",
                {},
            )

            if not isinstance(raw_details, dict):
                raise ValueError(f"{period_name}.details must be an object")

            precipitation_amount = raw_details.get(
                "precipitation_amount",
                0.0,
            )

            if isinstance(
                precipitation_amount,
                bool,
            ) or not isinstance(
                precipitation_amount,
                (
                    int,
                    float,
                ),
            ):
                raise ValueError(
                    f"{period_name}.details.precipitation_amount must be numeric"
                )

            return (
                float(precipitation_amount),
                normalized_symbol_code,
            )

        return None

    @staticmethod
    def _parse_datetime(
        raw_value: str,
    ) -> datetime:
        normalized_value = raw_value.strip()

        if normalized_value.endswith("Z"):
            normalized_value = f"{normalized_value[:-1]}+00:00"

        parsed_value = datetime.fromisoformat(normalized_value)

        if parsed_value.tzinfo is None:
            raise ValueError("forecast time must be timezone-aware")

        return parsed_value

    @staticmethod
    def _require_mapping(
        payload: dict[str, Any],
        key: str,
    ) -> dict[str, Any]:
        value = payload.get(key)

        if not isinstance(value, dict):
            raise ValueError(f"{key} must be an object")

        return value

    @staticmethod
    def _require_string(
        payload: dict[str, Any],
        key: str,
    ) -> str:
        value = payload.get(key)

        if not isinstance(value, str):
            raise ValueError(f"{key} must be a string")

        if not value.strip():
            raise ValueError(f"{key} cannot be empty")

        return value

    @staticmethod
    def _require_number(
        payload: dict[str, Any],
        key: str,
    ) -> float:
        value = payload.get(key)

        if isinstance(value, bool) or not isinstance(
            value,
            (
                int,
                float,
            ),
        ):
            raise ValueError(f"{key} must be numeric")

        return float(value)
