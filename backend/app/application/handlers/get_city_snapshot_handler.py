from datetime import timedelta

from app.application.queries import GetCitySnapshotQuery
from app.domain.decision import CitySnapshot
from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.geography import City, Coordinates, Zone
from app.domain.value_objects import Confidence, ImpactScore
from app.services.city_snapshot_service import CitySnapshotService


class GetCitySnapshotHandler:
    def __init__(
        self,
        city_snapshot_service: CitySnapshotService,
    ) -> None:
        self.city_snapshot_service = city_snapshot_service

    def handle(
        self,
        query: GetCitySnapshotQuery,
    ) -> CitySnapshot:
        city = self._build_demo_city(query.city_name)
        signals = self._build_demo_signals()

        return self.city_snapshot_service.create_snapshot(
            city=city,
            signals=signals,
        )

    def _build_demo_city(
        self,
        city_name: str,
    ) -> City:
        city = City(
            name=city_name,
            country="Bulgaria",
        )

        city.add_zone(
            Zone(
                name="Sofia Airport",
                city=city_name,
                country="Bulgaria",
                coordinates=Coordinates(
                    latitude=42.6967,
                    longitude=23.4114,
                ),
            )
        )

        city.add_zone(
            Zone(
                name="NDK",
                city=city_name,
                country="Bulgaria",
                coordinates=Coordinates(
                    latitude=42.6853,
                    longitude=23.3180,
                ),
            )
        )

        return city

    def _build_demo_signals(self) -> list[SignalEvent]:
        return [
            SignalEvent(
                source=SignalSource.AIRPORT,
                signal_type=SignalType.AIRPORT_ACTIVITY,
                zone_name="Sofia Airport",
                impact_score=ImpactScore(80.0),
                confidence=Confidence(0.95),
                priority=PriorityLevel.HIGH,
                ttl=timedelta(minutes=45),
                payload={"airport": "SOF"},
            ),
            SignalEvent(
                source=SignalSource.WEATHER,
                signal_type=SignalType.WEATHER_CONDITION,
                zone_name="Sofia Airport",
                impact_score=ImpactScore(40.0),
                confidence=Confidence(0.90),
                priority=PriorityLevel.MEDIUM,
                ttl=timedelta(hours=2),
                payload={"condition": "rain"},
            ),
            SignalEvent(
                source=SignalSource.EVENTS,
                signal_type=SignalType.EVENT_ACTIVITY,
                zone_name="NDK",
                impact_score=ImpactScore(95.0),
                confidence=Confidence(0.88),
                priority=PriorityLevel.HIGH,
                ttl=timedelta(hours=3),
                payload={"event": "concert"},
            ),
        ]
