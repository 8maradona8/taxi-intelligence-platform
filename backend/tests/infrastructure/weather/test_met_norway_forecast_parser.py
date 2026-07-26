import json
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pytest

from app.infrastructure.mappers import (
    MetNorwayForecastParser,
)


FIXTURE_PATH = (
    Path(__file__).parents[2]
    / "fixtures"
    / "weather"
    / "sofia_locationforecast_compact.json"
)


def load_fixture() -> dict[str, Any]:
    return json.loads(
        FIXTURE_PATH.read_text(
            encoding="utf-8",
        )
    )


def test_parser_reads_saved_real_fixture() -> None:
    parser = MetNorwayForecastParser()

    forecasts = parser.parse_forecasts(load_fixture())

    assert len(forecasts) == 88

    first = forecasts[0]

    assert first.forecast_at == datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )
    assert first.air_temperature_celsius == 29.7
    assert first.relative_humidity_percent == 32.8
    assert first.wind_speed_mps == 3.3
    assert first.wind_from_direction_degrees == 330.9
    assert first.cloud_area_fraction_percent == 4.7
    assert first.air_pressure_at_sea_level_hpa == 1015.7
    assert first.precipitation_amount_mm == 0.0
    assert first.symbol_code == "clearsky_day"


def test_parser_prefers_next_one_hour_period() -> None:
    payload = load_fixture()
    first_point = payload["properties"]["timeseries"][0]
    data = first_point["data"]

    data["next_1_hours"]["summary"]["symbol_code"] = "rainshowers_day"
    data["next_1_hours"]["details"]["precipitation_amount"] = 2.4

    data["next_6_hours"]["summary"]["symbol_code"] = "cloudy"
    data["next_6_hours"]["details"]["precipitation_amount"] = 8.0

    parser = MetNorwayForecastParser()

    forecast = parser.parse_forecasts(payload)[0]

    assert forecast.symbol_code == "rainshowers_day"
    assert forecast.precipitation_amount_mm == 2.4


def test_parser_falls_back_to_next_six_hours() -> None:
    payload = load_fixture()
    first_point = payload["properties"]["timeseries"][0]
    data = first_point["data"]

    data.pop("next_1_hours")

    parser = MetNorwayForecastParser()

    forecast = parser.parse_forecasts(payload)[0]

    assert forecast.symbol_code == "fair_day"
    assert forecast.precipitation_amount_mm == 0.0


def test_parser_defaults_missing_precipitation_to_zero() -> None:
    payload = load_fixture()
    first_point = payload["properties"]["timeseries"][0]
    next_one_hour = first_point["data"]["next_1_hours"]

    next_one_hour["details"] = {}

    parser = MetNorwayForecastParser()

    forecast = parser.parse_forecasts(payload)[0]

    assert forecast.precipitation_amount_mm == 0.0


def test_parser_rejects_missing_timeseries() -> None:
    parser = MetNorwayForecastParser()

    with pytest.raises(
        ValueError,
        match="timeseries must be a list",
    ):
        parser.parse_forecasts(
            {
                "type": "Feature",
                "properties": {},
            }
        )


def test_parser_rejects_empty_timeseries() -> None:
    parser = MetNorwayForecastParser()

    with pytest.raises(
        ValueError,
        match="contains no complete forecast points",
    ):
        parser.parse_forecasts(
            {
                "type": "Feature",
                "properties": {
                    "timeseries": [],
                },
            }
        )


def test_parser_reports_invalid_point_index() -> None:
    payload = load_fixture()
    payload["properties"]["timeseries"][0]["data"]["instant"]["details"].pop(
        "air_temperature"
    )

    parser = MetNorwayForecastParser()

    with pytest.raises(
        ValueError,
        match="forecast point at index 0",
    ):
        parser.parse_forecasts(payload)


def test_parser_skips_instant_only_forecast_point() -> None:
    payload = load_fixture()
    original_timeseries = payload["properties"]["timeseries"]

    first_point = original_timeseries[0]
    first_point["data"].pop(
        "next_1_hours",
        None,
    )
    first_point["data"].pop(
        "next_6_hours",
        None,
    )
    first_point["data"].pop(
        "next_12_hours",
        None,
    )

    parser = MetNorwayForecastParser()

    forecasts = parser.parse_forecasts(payload)

    assert len(forecasts) == 87
    assert forecasts[0].forecast_at != datetime(
        2026,
        7,
        21,
        12,
        0,
        tzinfo=UTC,
    )


def test_parser_rejects_malformed_existing_period() -> None:
    payload = load_fixture()
    first_point = payload["properties"]["timeseries"][0]

    first_point["data"]["next_1_hours"] = {
        "summary": {
            "symbol_code": 123,
        },
        "details": {},
    }

    parser = MetNorwayForecastParser()

    with pytest.raises(
        ValueError,
        match="forecast point at index 0",
    ):
        parser.parse_forecasts(payload)
