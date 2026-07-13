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


@pytest.mark.anyio
async def test_scheduler_tracks_successful_run() -> None:
    async def fake_job() -> SignalEvent:
        return make_signal()

    scheduler = AirportScheduler(
        job=fake_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    await scheduler.run_once()

    status = scheduler.status

    assert status.runs_total == 1
    assert status.successes_total == 1
    assert status.failures_total == 0
    assert status.last_success_at is not None
    assert status.last_failure_at is None
    assert status.last_error is None
    assert status.last_impact_score == 24.0
    assert status.last_arrivals == 2


@pytest.mark.anyio
async def test_scheduler_tracks_failed_run() -> None:
    async def failing_job() -> SignalEvent:
        raise RuntimeError("Airport source unavailable")

    scheduler = AirportScheduler(
        job=failing_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    with pytest.raises(
        RuntimeError,
        match="Airport source unavailable",
    ):
        await scheduler.run_once()

    status = scheduler.status

    assert status.runs_total == 1
    assert status.successes_total == 0
    assert status.failures_total == 1
    assert status.last_success_at is None
    assert status.last_failure_at is not None
    assert status.last_error == ("RuntimeError: Airport source unavailable")
