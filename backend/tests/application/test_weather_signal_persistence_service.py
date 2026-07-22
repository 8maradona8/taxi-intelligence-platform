from app.services.weather_signal_persistence_service import (
    WeatherSignalPersistenceService,
)


def test_weather_fingerprint_detects_relevant_changes() -> None:
    first = WeatherSignalPersistenceService._weather_payload_fingerprint(
        {
            "provider": "met-norway",
            "location": "Sofia",
            "forecast_count": 6,
            "current": {
                "forecast_at": ("2026-07-21T12:00:00+00:00"),
                "symbol_code": "fair_day",
                "air_temperature_celsius": 24.0,
                "relative_humidity_percent": 58.0,
                "wind_speed_mps": 3.0,
                "precipitation_amount_mm": 0.0,
            },
        }
    )

    second = WeatherSignalPersistenceService._weather_payload_fingerprint(
        {
            "provider": "met-norway",
            "location": "Sofia",
            "forecast_count": 6,
            "current": {
                "forecast_at": ("2026-07-21T12:00:00+00:00"),
                "symbol_code": "rain",
                "air_temperature_celsius": 22.0,
                "relative_humidity_percent": 78.0,
                "wind_speed_mps": 5.0,
                "precipitation_amount_mm": 2.5,
            },
        }
    )

    assert first != second


def test_weather_fingerprint_ignores_persistence_metadata() -> None:
    payload = {
        "provider": "met-norway",
        "location": "Sofia",
        "forecast_count": 6,
        "current": {
            "forecast_at": "2026-07-21T12:00:00+00:00",
            "symbol_code": "fair_day",
            "air_temperature_celsius": 24.0,
            "relative_humidity_percent": 58.0,
            "wind_speed_mps": 3.0,
            "precipitation_amount_mm": 0.0,
        },
    }

    stored_payload = {
        **payload,
        "confidence": 0.95,
        "priority": "low",
        "ttl_seconds": 1800,
    }

    fingerprint = WeatherSignalPersistenceService._weather_payload_fingerprint

    assert fingerprint(payload) == fingerprint(stored_payload)
