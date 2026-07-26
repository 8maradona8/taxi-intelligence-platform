from datetime import timedelta

from app.domain.decision import (
    CityDecisionEngine,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.geography import City, Coordinates, Zone
from app.domain.pipelines import SignalPipeline
from app.domain.value_objects import Confidence, ImpactScore
from app.services.city_snapshot_service import CitySnapshotService


city = City(
    name="Sofia",
    country="Bulgaria",
)

city.add_zone(
    Zone(
        name="Sofia Airport",
        city="Sofia",
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
        city="Sofia",
        country="Bulgaria",
        coordinates=Coordinates(
            latitude=42.6853,
            longitude=23.3180,
        ),
    )
)

signals = [
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

snapshot_service = CitySnapshotService(
    signal_pipeline=SignalPipeline(),
    city_decision_engine=CityDecisionEngine(),
    opportunity_engine=OpportunityEngine(),
    recommendation_engine=RecommendationEngine(),
)

snapshot = snapshot_service.create_snapshot(
    city=city,
    signals=signals,
)

print("City:", snapshot.city_name)
print("Opportunities:", snapshot.opportunity_count)
print("Has recommendation:", snapshot.has_recommendation)

if snapshot.best_recommendation:
    print("Best recommendation:", snapshot.best_recommendation.summary)
    print("Urgency:", snapshot.best_recommendation.urgency)
    print("Confidence:", snapshot.best_recommendation.confidence_percent)

print("Ranked zones:")
for index, opportunity in enumerate(snapshot.opportunities, start=1):
    print(f"{index}. {opportunity.zone_name} — {opportunity.score}")
