from datetime import UTC, datetime, timedelta
from types import SimpleNamespace
from typing import Any

import pytest

from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import (
    Confidence,
    ImpactScore,
)
from app.services.signal_persistence_service import (
    SignalPersistenceService,
    SignalZoneConfiguration,
)


class FakeZoneRepository:
    def __init__(self) -> None:
        self.zone = None
        self.created_values: dict[str, object] | None = None

    async def get_by_name(
        self,
        name: str,
    ) -> object | None:
        assert name == "Test Zone"

        return self.zone

    async def create(
        self,
        *,
        name: str,
        city: str,
        country: str,
        latitude: float,
        longitude: float,
    ) -> object:
        self.created_values = {
            "name": name,
            "city": city,
            "country": country,
            "latitude": latitude,
            "longitude": longitude,
        }

        self.zone = SimpleNamespace(id=7)

        return self.zone


class FakeSignalRepository:
    def __init__(self) -> None:
        self.existing_signal = None
        self.created_values: dict[str, object] | None = None

    async def get_latest_since(
        self,
        *,
        signal_type: str,
        source: str,
        zone_id: int,
        observed_since: datetime,
    ) -> object | None:
        assert signal_type == "transport_activity"
        assert source == "transport"
        assert zone_id == 7
        assert observed_since.tzinfo is not None

        return self.existing_signal

    async def create(
        self,
        **values: object,
    ) -> object:
        self.created_values = values

        return SimpleNamespace(
            id=11,
            **values,
        )


def make_signal() -> SignalEvent:
    return SignalEvent(
        source=SignalSource.TRANSPORT,
        signal_type=(SignalType.TRANSPORT_ACTIVITY),
        zone_name="Test Zone",
        impact_score=ImpactScore(42.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.MEDIUM,
        observed_at=datetime(
            2026,
            7,
            17,
            9,
            0,
            tzinfo=UTC,
        ),
        ttl=timedelta(minutes=15),
        payload={
            "mode": "railway",
            "train_numbers": ["2626"],
            "arrivals": 1,
        },
    )


def fingerprint(
    payload: dict[str, Any],
) -> tuple[object, ...]:
    return (
        payload.get("mode"),
        tuple(payload.get("train_numbers", [])),
        payload.get("arrivals"),
    )


@pytest.mark.anyio
async def test_generic_persistence_creates_zone_and_signal() -> None:
    zone_repository = FakeZoneRepository()
    signal_repository = FakeSignalRepository()

    service = SignalPersistenceService(
        zone_repository=(
            zone_repository  # type: ignore[arg-type]
        ),
        signal_repository=(
            signal_repository  # type: ignore[arg-type]
        ),
        zone_configuration=SignalZoneConfiguration(
            city="Sofia",
            country="Bulgaria",
            latitude=42.70,
            longitude=23.32,
        ),
        payload_fingerprint=fingerprint,
    )

    result = await service.persist(make_signal())

    assert result.id == 11

    assert zone_repository.created_values == {
        "name": "Test Zone",
        "city": "Sofia",
        "country": "Bulgaria",
        "latitude": 42.70,
        "longitude": 23.32,
    }

    created_values = signal_repository.created_values

    assert created_values is not None
    assert created_values["zone_id"] == 7
    assert created_values["impact_score"] == 42.0

    payload = created_values["payload"]

    assert isinstance(payload, dict)
    assert payload["confidence"] == 0.95
    assert payload["priority"] == "medium"
    assert payload["ttl_seconds"] == 900


@pytest.mark.anyio
async def test_generic_persistence_returns_duplicate_signal() -> None:
    zone_repository = FakeZoneRepository()
    zone_repository.zone = SimpleNamespace(id=7)

    signal_repository = FakeSignalRepository()
    existing_signal = SimpleNamespace(
        id=9,
        payload={
            "mode": "railway",
            "train_numbers": ["2626"],
            "arrivals": 1,
        },
    )
    signal_repository.existing_signal = existing_signal

    service = SignalPersistenceService(
        zone_repository=(
            zone_repository  # type: ignore[arg-type]
        ),
        signal_repository=(
            signal_repository  # type: ignore[arg-type]
        ),
        zone_configuration=SignalZoneConfiguration(
            city="Sofia",
            country="Bulgaria",
            latitude=42.70,
            longitude=23.32,
        ),
        payload_fingerprint=fingerprint,
    )

    result = await service.persist(make_signal())

    assert result is existing_signal
    assert signal_repository.created_values is None


def test_zone_configuration_validates_coordinates() -> None:
    with pytest.raises(
        ValueError,
        match="latitude must be between",
    ):
        SignalZoneConfiguration(
            city="Sofia",
            country="Bulgaria",
            latitude=100.0,
            longitude=23.32,
        )
