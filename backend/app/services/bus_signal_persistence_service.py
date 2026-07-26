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


class BusSignalPersistenceService(SignalPersistenceService):
    SOFIA_CENTRAL_BUS_STATION_LATITUDE = 42.7103411
    SOFIA_CENTRAL_BUS_STATION_LONGITUDE = 23.3232328

    def __init__(
        self,
        *,
        zone_repository: ZoneRepository,
        signal_repository: SignalRepository,
        deduplication_window: timedelta = timedelta(minutes=5),
    ) -> None:
        super().__init__(
            zone_repository=zone_repository,
            signal_repository=signal_repository,
            zone_configuration=SignalZoneConfiguration(
                city="Sofia",
                country="Bulgaria",
                latitude=(self.SOFIA_CENTRAL_BUS_STATION_LATITUDE),
                longitude=(self.SOFIA_CENTRAL_BUS_STATION_LONGITUDE),
            ),
            payload_fingerprint=(self._bus_payload_fingerprint),
            deduplication_window=deduplication_window,
        )

    @staticmethod
    def _bus_payload_fingerprint(
        payload: dict[str, Any],
    ) -> tuple[object, ...]:
        return (
            payload.get("mode"),
            payload.get("station_code"),
            tuple(payload.get("arrival_times", [])),
            tuple(payload.get("routes", [])),
            tuple(payload.get("carriers", [])),
            payload.get("arrivals"),
            payload.get("unique_origins"),
            payload.get("known_sectors"),
        )
