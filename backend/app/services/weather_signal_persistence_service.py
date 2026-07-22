from datetime import timedelta
from typing import Any

from app.repositories import (
    SignalRepository,
    ZoneRepository,
)
from app.services.signal_persistence_service import (
    SignalPersistenceService,
    SignalZoneConfiguration,
)


class WeatherSignalPersistenceService(
    SignalPersistenceService,
):
    SOFIA_LATITUDE = 42.6977
    SOFIA_LONGITUDE = 23.3219

    def __init__(
        self,
        *,
        zone_repository: ZoneRepository,
        signal_repository: SignalRepository,
        deduplication_window: timedelta = timedelta(
            minutes=15,
        ),
    ) -> None:
        super().__init__(
            zone_repository=zone_repository,
            signal_repository=signal_repository,
            zone_configuration=SignalZoneConfiguration(
                city="Sofia",
                country="Bulgaria",
                latitude=self.SOFIA_LATITUDE,
                longitude=self.SOFIA_LONGITUDE,
            ),
            payload_fingerprint=(self._weather_payload_fingerprint),
            deduplication_window=deduplication_window,
        )

    @staticmethod
    def _weather_payload_fingerprint(
        payload: dict[str, Any],
    ) -> tuple[object, ...]:
        current = payload.get("current")

        if not isinstance(current, dict):
            current = {}

        return (
            payload.get("provider"),
            payload.get("location"),
            current.get("forecast_at"),
            current.get("symbol_code"),
            current.get("air_temperature_celsius"),
            current.get("relative_humidity_percent"),
            current.get("wind_speed_mps"),
            current.get("precipitation_amount_mm"),
            payload.get("forecast_count"),
        )
