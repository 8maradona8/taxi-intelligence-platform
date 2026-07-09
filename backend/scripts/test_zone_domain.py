from datetime import timedelta

from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.geography import Coordinates, Zone
from app.domain.value_objects import Confidence, ImpactScore


zone = Zone(
    name="Sofia Airport",
    city="Sofia",
    country="Bulgaria",
    coordinates=Coordinates(
        latitude=42.6967,
        longitude=23.4114,
    ),
)

signal = SignalEvent(
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
)

zone.add_signal(signal)

print("Zone:", zone.name)
print("Active signals:", len(zone.active_signals()))
print("Total impact:", zone.total_impact_score())
print("Average confidence:", zone.average_confidence())