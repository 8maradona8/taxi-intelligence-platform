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
from app.schedulers import RailwayScheduler


def make_signal() -> SignalEvent:
    return SignalEvent(
        source=SignalSource.TRANSPORT,
        signal_type=(SignalType.TRANSPORT_ACTIVITY),
        zone_name=("Sofia Central Railway Station"),
        impact_score=ImpactScore(42.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.MEDIUM,
        ttl=timedelta(minutes=15),
        payload={
            "mode": "railway",
            "arrivals": 3,
        },
    )


@pytest.mark.anyio
async def test_railway_scheduler_executes_job() -> None:
    calls = 0

    async def fake_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        return make_signal()

    scheduler = RailwayScheduler(
        job=fake_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    signal = await scheduler.run_once()

    assert signal is not None
    assert calls == 1
    assert scheduler.status.name == ("railway-signal-scheduler")
    assert scheduler.status.successes_total == 1
    assert scheduler.status.last_arrivals == 3
    assert scheduler.status.last_impact_score == 42.0


@pytest.mark.anyio
async def test_railway_scheduler_tracks_failure() -> None:
    async def failing_job() -> SignalEvent:
        raise RuntimeError("BDZ source unavailable")

    scheduler = RailwayScheduler(
        job=failing_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    with pytest.raises(
        RuntimeError,
        match="BDZ source unavailable",
    ):
        await scheduler.run_once()

    assert scheduler.status.failures_total == 1
    assert scheduler.status.last_error == ("RuntimeError: BDZ source unavailable")
