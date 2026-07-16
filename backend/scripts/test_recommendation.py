from datetime import timedelta

from app.domain.decision import DecisionEngine, Recommendation, RecommendationUrgency
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

decision = DecisionEngine().evaluate_zone(zone)

recommendation = Recommendation(
    title="Move to Sofia Airport",
    zone_name=decision.zone.name,
    action=decision.action,
    urgency=RecommendationUrgency.HIGH,
    demand_level=decision.demand_score.level,
    confidence=decision.confidence,
    reasons=decision.reasons,
    valid_until=decision.zone.active_signals()[0].expires_at,
)

print("Title:", recommendation.title)
print("Summary:", recommendation.summary)
print("Zone:", recommendation.zone_name)
print("Urgency:", recommendation.urgency)
print("Demand:", recommendation.demand_level)
print("Confidence:", recommendation.confidence_percent)
print("Reasons:", recommendation.reason_count)
