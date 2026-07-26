from datetime import UTC, datetime, timedelta
from types import SimpleNamespace

import pytest

from app.domain.enums import PriorityLevel
from app.services.airport_signal_read_service import (
    AirportSignalReadService,
)


class FakeZoneRepository:
    def __init__(self, zone: object | None) -> None:
        self._zone = zone

    async def get_by_name(
        self,
        name: str,
    ) -> object | None:
        assert name == "Sofia Airport"

        return self._zone


class FakeSignalRepository:
    def __init__(
        self,
        signals: list[object],
    ) -> None:
        self._signals = signals

    async def list_latest(
        self,
        *,
        signal_type: str,
        source: str,
        zone_id: int,
        limit: int,
    ) -> list[object]:
        assert signal_type == "airport_activity"
        assert source == "airport"
        assert zone_id == 1
        assert limit == 20

        return self._signals


def make_stored_signal(
    *,
    observed_at: datetime,
    ttl_seconds: int = 900,
    impact_score: float = 48.0,
) -> object:
    return SimpleNamespace(
        id=10,
        impact_score=impact_score,
        observed_at=observed_at,
        payload={
            "airport": "SOF",
            "arrivals": 4,
            "scheduled": 2,
            "expected": 1,
            "delayed": 1,
            "cancelled": 0,
            "confidence": 0.95,
            "priority": "medium",
            "ttl_seconds": ttl_seconds,
            "flight_numbers": [
                "FR100",
                "W6100",
            ],
        },
    )


@pytest.mark.anyio
async def test_read_service_returns_active_signal() -> None:
    now = datetime(
        2026,
        7,
        13,
        12,
        0,
        tzinfo=UTC,
    )

    stored_signal = make_stored_signal(
        observed_at=now - timedelta(minutes=5),
    )

    service = AirportSignalReadService(
        zone_repository=FakeZoneRepository(
            SimpleNamespace(
                id=1,
                name="Sofia Airport",
            )
        ),
        signal_repository=FakeSignalRepository([stored_signal]),
    )

    signal = await service.get_latest_active_signal(now=now)

    assert signal is not None
    assert signal.zone_name == "Sofia Airport"
    assert signal.impact_score.value == 48.0
    assert signal.confidence.value == 0.95
    assert signal.priority == PriorityLevel.MEDIUM
    assert signal.payload["arrivals"] == 4
    assert signal.payload["flight_numbers"] == [
        "FR100",
        "W6100",
    ]


@pytest.mark.anyio
async def test_read_service_ignores_expired_signal() -> None:
    now = datetime(
        2026,
        7,
        13,
        12,
        0,
        tzinfo=UTC,
    )

    stored_signal = make_stored_signal(
        observed_at=now - timedelta(minutes=20),
        ttl_seconds=900,
    )

    service = AirportSignalReadService(
        zone_repository=FakeZoneRepository(
            SimpleNamespace(
                id=1,
                name="Sofia Airport",
            )
        ),
        signal_repository=FakeSignalRepository([stored_signal]),
    )

    signal = await service.get_latest_active_signal(now=now)

    assert signal is None


@pytest.mark.anyio
async def test_read_service_returns_none_without_zone() -> None:
    service = AirportSignalReadService(
        zone_repository=FakeZoneRepository(None),
        signal_repository=FakeSignalRepository([]),
    )

    signal = await service.get_latest_active_signal()

    assert signal is None
