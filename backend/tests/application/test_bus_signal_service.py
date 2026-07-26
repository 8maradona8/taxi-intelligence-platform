from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domain import BusArrival
from app.domain.events import SignalEvent
from app.infrastructure.mappers import BusSignalMapper
from app.services.bus_signal_service import (
    BusSignalService,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class FakeBusCollector:
    def __init__(self) -> None:
        self.received_observed_at: datetime | None = None

    async def collect_arrivals(
        self,
        *,
        observed_at: datetime | None = None,
    ) -> list[BusArrival]:
        self.received_observed_at = observed_at

        assert observed_at is not None

        return [
            BusArrival(
                origin="ВАРНА",
                route="ВАРНА - СОФИЯ",
                full_route=("ВАРНА - В.ТЪРНОВО - СОФИЯ"),
                carrier="ГЛОБАЛ БИОМЕТ ЕООД",
                scheduled_arrival=(observed_at + timedelta(minutes=30)),
                operating_days=(
                    "пн",
                    "вт",
                    "ср",
                    "чт",
                    "пк",
                    "сб",
                    "нд",
                ),
                sector="12",
            )
        ]


class FakePersistenceService:
    def __init__(self) -> None:
        self.persisted_signal: SignalEvent | None = None

    async def persist(
        self,
        signal: SignalEvent,
    ) -> object:
        self.persisted_signal = signal

        return object()


@pytest.mark.anyio
async def test_bus_signal_service_creates_and_persists_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    collector = FakeBusCollector()
    persistence_service = FakePersistenceService()

    service = BusSignalService(
        collector=collector,  # type: ignore[arg-type]
        signal_mapper=BusSignalMapper(),
        persistence_service=(
            persistence_service  # type: ignore[arg-type]
        ),
    )

    signal = await service.create_arrivals_signal(
        observed_at=observed_at,
    )

    assert collector.received_observed_at == (observed_at)

    assert signal.zone_name == ("Sofia Central Bus Station")
    assert signal.payload["mode"] == "bus"
    assert signal.payload["arrivals"] == 1
    assert signal.payload["origins"] == [
        "ВАРНА",
    ]
    assert signal.payload["known_sectors"] == 1

    assert persistence_service.persisted_signal is signal


@pytest.mark.anyio
async def test_bus_signal_service_supports_no_persistence() -> None:
    observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    service = BusSignalService(
        collector=(
            FakeBusCollector()  # type: ignore[arg-type]
        ),
        signal_mapper=BusSignalMapper(),
    )

    signal = await service.create_arrivals_signal(
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 1
    assert signal.payload["mode"] == "bus"


@pytest.mark.anyio
async def test_bus_signal_service_normalizes_naive_time() -> None:
    naive_observed_at = datetime(
        2026,
        7,
        20,
        10,
        0,
    )

    collector = FakeBusCollector()

    service = BusSignalService(
        collector=collector,  # type: ignore[arg-type]
        signal_mapper=BusSignalMapper(),
    )

    signal = await service.create_arrivals_signal(
        observed_at=naive_observed_at,
    )

    assert collector.received_observed_at is not None
    assert collector.received_observed_at.tzinfo == SOFIA_TIMEZONE

    assert signal.observed_at == datetime(
        2026,
        7,
        20,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )
