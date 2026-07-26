from datetime import timedelta

from app.domain.decision import (
    CityDecisionEngine,
    CitySnapshot,
    OpportunityEngine,
    RecommendationEngine,
)
from app.domain.enums import PriorityLevel, SignalSource, SignalType
from app.domain.events import SignalEvent
from app.domain.geography import City, Coordinates, Zone
from app.domain.pipelines import SignalPipeline
from app.domain.value_objects import Confidence, ImpactScore


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

SignalPipeline().process_city(
    city=city,
    signals=signals,
)

decisions = CityDecisionEngine().evaluate_city(city)
opportunities = OpportunityEngine().rank(decisions)
best_recommendation = RecommendationEngine().recommend_best(opportunities)

snapshot = CitySnapshot.create(
    city_name=city.name,
    opportunities=opportunities,
    best_recommendation=best_recommendation,
)

print("City:", snapshot.city_name)
print("Generated at:", snapshot.generated_at)
print("Opportunities:", snapshot.opportunity_count)
print("Has recommendation:", snapshot.has_recommendation)

if snapshot.best_recommendation:
    print("Best recommendation:", snapshot.best_recommendation.summary)

print("Ranked zones:")
for index, opportunity in enumerate(snapshot.opportunities, start=1):
    print(f"{index}. {opportunity.zone_name} — {opportunity.score}")
