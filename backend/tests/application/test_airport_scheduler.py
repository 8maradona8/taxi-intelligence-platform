import asyncio
from datetime import timedelta

import pytest

from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore
from app.schedulers import AirportScheduler


def make_signal() -> SignalEvent:
    return SignalEvent(
        source=SignalSource.AIRPORT,
        signal_type=SignalType.AIRPORT_ACTIVITY,
        zone_name="Sofia Airport",
        impact_score=ImpactScore(24.0),
        confidence=Confidence(0.95),
        priority=PriorityLevel.LOW,
        ttl=timedelta(minutes=15),
        payload={
            "airport": "SOF",
            "arrivals": 2,
        },
    )


@pytest.mark.anyio
async def test_scheduler_run_once_executes_job() -> None:
    calls = 0

    async def fake_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        return make_signal()

    scheduler = AirportScheduler(
        job=fake_job,
        interval_seconds=300,
    )

    signal = await scheduler.run_once()

    assert calls == 1
    assert signal.zone_name == "Sofia Airport"
    assert signal.payload["arrivals"] == 2


@pytest.mark.anyio
async def test_scheduler_runs_on_startup() -> None:
    job_called = asyncio.Event()

    async def fake_job() -> SignalEvent:
        job_called.set()

        return make_signal()

    scheduler = AirportScheduler(
        job=fake_job,
        interval_seconds=300,
        run_on_startup=True,
    )

    await scheduler.start()

    try:
        await asyncio.wait_for(
            job_called.wait(),
            timeout=1.0,
        )

        assert scheduler.is_running is True
    finally:
        await scheduler.stop()

    assert scheduler.is_running is False


@pytest.mark.anyio
async def test_scheduler_does_not_start_twice() -> None:
    async def fake_job() -> SignalEvent:
        return make_signal()

    scheduler = AirportScheduler(
        job=fake_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    await scheduler.start()
    first_task = scheduler._task

    await scheduler.start()

    try:
        assert scheduler._task is first_task
    finally:
        await scheduler.stop()
