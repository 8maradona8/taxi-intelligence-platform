from datetime import timedelta

from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.geography import Coordinates, Zone
from app.domain.pipelines import SignalPipeline
from app.domain.value_objects import Confidence, ImpactScore


pipeline = SignalPipeline()

airport_zone = Zone(
    name="Sofia Airport",
    city="Sofia",
    country="Bulgaria",
    coordinates=Coordinates(
        latitude=42.6967,
        longitude=23.4114,
    ),
)

pipeline.register_zone(airport_zone)

signals = [
    SignalEvent(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        zone_name="Sofia Airport",
        impact_score=ImpactScore(33.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.HIGH,
        ttl=timedelta(minutes=45),
        payload={
            "airport": "SOF",
            "arrivals": 3,
            "departures": 1,
        },
    ),
    SignalEvent(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        zone_name="Sofia Airport",
        impact_score=ImpactScore(20.0),
        confidence=Confidence(0.90),
        priority=PriorityLevel.MEDIUM,
        ttl=timedelta(hours=2),
        payload={
            "condition": "rain",
        },
    ),
]

zones = pipeline.process(signals)

for zone in zones:
    print("Zone:", zone.name)
    print("Active signals:", len(zone.active_signals()))
    print("Total impact:", zone.total_impact_score())
    print("Average confidence:", zone.average_confidence())