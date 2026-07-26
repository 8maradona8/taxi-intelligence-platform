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


class AirportSignalPersistenceService(SignalPersistenceService):
    SOFIA_AIRPORT_LATITUDE = 42.6967
    SOFIA_AIRPORT_LONGITUDE = 23.4114

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
                latitude=(self.SOFIA_AIRPORT_LATITUDE),
                longitude=(self.SOFIA_AIRPORT_LONGITUDE),
            ),
            payload_fingerprint=(self._airport_payload_fingerprint),
            deduplication_window=(deduplication_window),
        )

    @staticmethod
    def _airport_payload_fingerprint(
        payload: dict[str, Any],
    ) -> tuple[object, ...]:
        return (
            tuple(payload.get("flight_numbers", [])),
            payload.get("arrivals"),
            payload.get("delayed"),
            payload.get("expected"),
        )
