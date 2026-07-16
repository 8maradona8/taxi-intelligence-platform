from datetime import timedelta

from app.domain.decision import DecisionEngine
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

zone.add_signal(
    SignalEvent(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        zone_name="Sofia Airport",
        impact_score=ImpactScore(80.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.HIGH,
        ttl=timedelta(minutes=45),
        payload={"airport": "SOF"},
    )
)

zone.add_signal(
    SignalEvent(
        source=SignalSource.WEATHER,
        signal_type=SignalType.WEATHER_CONDITION,
        zone_name="Sofia Airport",
        impact_score=ImpactScore(45.0),
        confidence=Confidence(0.90),
        priority=PriorityLevel.MEDIUM,
        ttl=timedelta(hours=2),
        payload={"condition": "rain"},
    )
)

engine = DecisionEngine()
decision = engine.evaluate_zone(zone)

print("Zone:", decision.zone.name)
print("Action:", decision.action)
print("Demand level:", decision.demand_score.level)
print("Score:", decision.demand_score.score)
print("Confidence:", decision.confidence)
print("Reasons:")
for reason in decision.reasons:
    print(f"- {reason.source}: {reason.description} ({reason.contribution})")
