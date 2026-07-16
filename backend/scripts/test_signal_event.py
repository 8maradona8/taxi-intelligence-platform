from datetime import timedelta

from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore


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

print(signal)
print("Expires at:", signal.expires_at)
print("Expired:", signal.is_expired)
