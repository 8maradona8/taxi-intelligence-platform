from datetime import timedelta

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
from app.schedulers import BusScheduler


def make_signal() -> SignalEvent:
    return SignalEvent(
        source=SignalSource.TRANSPORT,
        signal_type=SignalType.TRANSPORT_ACTIVITY,
        zone_name="Sofia Central Bus Station",
        impact_score=ImpactScore(38.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.LOW,
        ttl=timedelta(minutes=15),
        payload={
            "mode": "bus",
            "arrivals": 3,
        },
    )


@pytest.mark.anyio
async def test_bus_scheduler_executes_job() -> None:
    calls = 0

    async def fake_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        return make_signal()

    scheduler = BusScheduler(
        job=fake_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    signal = await scheduler.run_once()

    assert signal is not None
    assert calls == 1
    assert scheduler.status.name == ("bus-signal-scheduler")
    assert scheduler.status.successes_total == 1
    assert scheduler.status.last_arrivals == 3
    assert scheduler.status.last_impact_score == 38.0


@pytest.mark.anyio
async def test_bus_scheduler_tracks_failure() -> None:
    async def failing_job() -> SignalEvent:
        raise RuntimeError("Bus station source unavailable")

    scheduler = BusScheduler(
        job=failing_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    with pytest.raises(
        RuntimeError,
        match="Bus station source unavailable",
    ):
        await scheduler.run_once()

    assert scheduler.status.failures_total == 1
    assert scheduler.status.last_error == (
        "RuntimeError: Bus station source unavailable"
    )
