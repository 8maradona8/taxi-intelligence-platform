from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app.domain import TrainArrival, TrainStatus
from app.domain.events import SignalEvent
from app.infrastructure.mappers import (
    RailwaySignalMapper,
)
from app.services.railway_signal_service import (
    RailwaySignalService,
)


SOFIA_TIMEZONE = ZoneInfo("Europe/Sofia")


class FakeRailwayCollector:
    def __init__(self) -> None:
        self.received_service_date: date | None = None

    async def collect_arrivals(
        self,
        *,
        service_date: date,
    ) -> list[TrainArrival]:
        self.received_service_date = service_date

        observed_at = datetime(
            2026,
            7,
            17,
            10,
            0,
            tzinfo=SOFIA_TIMEZONE,
        )

        return [
            TrainArrival(
                train_number="2626",
                train_type_code="БВ",
                train_type_name="Бърз влак",
                origin_station="Варна",
                scheduled_arrival=(observed_at + timedelta(minutes=30)),
                status=TrainStatus.SCHEDULED,
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
async def test_railway_signal_service_creates_and_persists_signal() -> None:
    observed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    collector = FakeRailwayCollector()
    persistence_service = FakePersistenceService()

    service = RailwaySignalService(
        collector=collector,  # type: ignore[arg-type]
        signal_mapper=RailwaySignalMapper(),
        persistence_service=(
            persistence_service  # type: ignore[arg-type]
        ),
    )

    signal = await service.create_arrivals_signal(
        observed_at=observed_at,
    )

    assert collector.received_service_date == date(
        2026,
        7,
        17,
    )

    assert signal.zone_name == ("Sofia Central Railway Station")
    assert signal.payload["mode"] == "railway"
    assert signal.payload["arrivals"] == 1

    assert persistence_service.persisted_signal is signal


@pytest.mark.anyio
async def test_railway_signal_service_supports_no_persistence() -> None:
    observed_at = datetime(
        2026,
        7,
        17,
        10,
        0,
        tzinfo=SOFIA_TIMEZONE,
    )

    service = RailwaySignalService(
        collector=(
            FakeRailwayCollector()  # type: ignore[arg-type]
        ),
        signal_mapper=RailwaySignalMapper(),
    )

    signal = await service.create_arrivals_signal(
        observed_at=observed_at,
    )

    assert signal.payload["arrivals"] == 1
