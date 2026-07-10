from collections.abc import Iterator
from datetime import timedelta

import pytest
from fastapi.testclient import TestClient

from app.application.handlers import GetCitySnapshotHandler
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
from app.main import app
from app.services.city_snapshot_service import CitySnapshotService


@pytest.fixture
def sofia_city() -> City:
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

    return city


@pytest.fixture
def city_signals() -> list[SignalEvent]:
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


@pytest.fixture
def snapshot_service() -> CitySnapshotService:
    return CitySnapshotService(
        signal_pipeline=SignalPipeline(),
        city_decision_engine=CityDecisionEngine(),
        opportunity_engine=OpportunityEngine(),
        recommendation_engine=RecommendationEngine(),
    )


@pytest.fixture
def snapshot_handler(
    snapshot_service: CitySnapshotService,
) -> GetCitySnapshotHandler:
    return GetCitySnapshotHandler(
        city_snapshot_service=snapshot_service,
    )


@pytest.fixture
def api_client() -> Iterator[TestClient]:
    with TestClient(app) as client:
        yield client
