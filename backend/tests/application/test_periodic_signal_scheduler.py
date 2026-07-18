import asyncio
from datetime import timedelta

import pytest

from app.application.interfaces import SchedulerRunRecord
from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore
from app.infrastructure.http import (
    HttpResponseError,
    HttpTimeoutError,
)
from app.schedulers import PeriodicSignalScheduler


SCHEDULER_NAME = "test-signal-scheduler"


class FakeSchedulerRunRecorder:
    def __init__(self) -> None:
        self.records: list[SchedulerRunRecord] = []

    async def record(
        self,
        run: SchedulerRunRecord,
    ) -> None:
        self.records.append(run)


def make_signal(
    *,
    arrivals: int = 3,
    impact_score: float = 42.0,
) -> SignalEvent:
    return SignalEvent(
        source=SignalSource.TRANSPORT,
        signal_type=SignalType.TRANSPORT_ACTIVITY,
        zone_name="Test Transport Zone",
        impact_score=ImpactScore(impact_score),
        confidence=Confidence(0.95),
        priority=PriorityLevel.MEDIUM,
        ttl=timedelta(minutes=15),
        payload={
            "arrivals": arrivals,
        },
    )


def test_scheduler_rejects_empty_name() -> None:
    async def fake_job() -> SignalEvent:
        return make_signal()

    with pytest.raises(
        ValueError,
        match="scheduler name cannot be empty",
    ):
        PeriodicSignalScheduler(
            name="   ",
            job=fake_job,
        )


def test_scheduler_rejects_invalid_configuration() -> None:
    async def fake_job() -> SignalEvent:
        return make_signal()

    with pytest.raises(
        ValueError,
        match="interval_seconds must be greater than zero",
    ):
        PeriodicSignalScheduler(
            name=SCHEDULER_NAME,
            job=fake_job,
            interval_seconds=0,
        )

    with pytest.raises(
        ValueError,
        match="max_attempts must be greater than zero",
    ):
        PeriodicSignalScheduler(
            name=SCHEDULER_NAME,
            job=fake_job,
            max_attempts=0,
        )

    with pytest.raises(
        ValueError,
        match="retry_backoff_seconds cannot be negative",
    ):
        PeriodicSignalScheduler(
            name=SCHEDULER_NAME,
            job=fake_job,
            retry_backoff_seconds=-1,
        )


@pytest.mark.anyio
async def test_scheduler_executes_job_and_tracks_success() -> None:
    calls = 0

    async def fake_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        return make_signal(
            arrivals=4,
            impact_score=56.0,
        )

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
        job=fake_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    signal = await scheduler.run_once()

    assert signal is not None
    assert calls == 1

    status = scheduler.status

    assert status.name == SCHEDULER_NAME
    assert status.runs_total == 1
    assert status.successes_total == 1
    assert status.failures_total == 0
    assert status.last_success_at is not None
    assert status.last_failure_at is None
    assert status.last_error is None
    assert status.last_arrivals == 4
    assert status.last_impact_score == 56.0


@pytest.mark.anyio
async def test_scheduler_tracks_failure() -> None:
    async def failing_job() -> SignalEvent:
        raise RuntimeError("Source unavailable")

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
        job=failing_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    with pytest.raises(
        RuntimeError,
        match="Source unavailable",
    ):
        await scheduler.run_once()

    status = scheduler.status

    assert status.runs_total == 1
    assert status.successes_total == 0
    assert status.failures_total == 1
    assert status.last_success_at is None
    assert status.last_failure_at is not None
    assert status.last_error == "RuntimeError: Source unavailable"


@pytest.mark.anyio
async def test_scheduler_retries_temporary_failure() -> None:
    calls = 0

    async def temporary_failure_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        if calls == 1:
            raise HttpTimeoutError("Temporary timeout")

        return make_signal()

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
        job=temporary_failure_job,
        interval_seconds=300,
        run_on_startup=False,
        max_attempts=2,
        retry_backoff_seconds=0,
    )

    signal = await scheduler.run_once()

    assert signal is not None
    assert calls == 2
    assert scheduler.status.successes_total == 1
    assert scheduler.status.failures_total == 0
    assert scheduler.status.retry_attempts_total == 1
    assert scheduler.status.recovering is False


@pytest.mark.anyio
async def test_scheduler_does_not_retry_permanent_http_error() -> None:
    calls = 0

    async def failing_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        raise HttpResponseError(
            status_code=404,
            message="Not Found",
        )

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
        job=failing_job,
        interval_seconds=300,
        run_on_startup=False,
        max_attempts=3,
        retry_backoff_seconds=0,
    )

    with pytest.raises(HttpResponseError):
        await scheduler.run_once()

    assert calls == 1
    assert scheduler.status.retry_attempts_total == 0
    assert scheduler.status.failures_total == 1


@pytest.mark.anyio
async def test_scheduler_skips_overlapping_execution() -> None:
    job_started = asyncio.Event()
    allow_completion = asyncio.Event()

    async def slow_job() -> SignalEvent:
        job_started.set()
        await allow_completion.wait()

        return make_signal()

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
        job=slow_job,
        interval_seconds=300,
        run_on_startup=False,
    )

    first_run = asyncio.create_task(scheduler.run_once())

    await asyncio.wait_for(
        job_started.wait(),
        timeout=1.0,
    )

    second_result = await scheduler.run_once()

    assert second_result is None
    assert scheduler.status.overlap_skips_total == 1

    allow_completion.set()

    first_result = await first_run

    assert first_result is not None
    assert scheduler.status.successes_total == 1


@pytest.mark.anyio
async def test_scheduler_records_successful_run() -> None:
    recorder = FakeSchedulerRunRecorder()

    async def fake_job() -> SignalEvent:
        return make_signal(
            arrivals=5,
            impact_score=68.0,
        )

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
        job=fake_job,
        interval_seconds=300,
        run_on_startup=False,
        run_recorder=recorder,
    )

    await scheduler.run_once()

    assert len(recorder.records) == 1

    record = recorder.records[0]

    assert record.scheduler_name == SCHEDULER_NAME
    assert record.status == "success"
    assert record.attempts == 1
    assert record.retry_attempts == 0
    assert record.arrivals == 5
    assert record.impact_score == 68.0
    assert record.error_type is None
    assert record.error_message is None
    assert record.duration_ms >= 0


@pytest.mark.anyio
async def test_scheduler_records_failed_run() -> None:
    recorder = FakeSchedulerRunRecorder()

    async def failing_job() -> SignalEvent:
        raise ValueError("Invalid signal state")

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
        job=failing_job,
        interval_seconds=300,
        run_on_startup=False,
        run_recorder=recorder,
    )

    with pytest.raises(
        ValueError,
        match="Invalid signal state",
    ):
        await scheduler.run_once()

    assert len(recorder.records) == 1

    record = recorder.records[0]

    assert record.scheduler_name == SCHEDULER_NAME
    assert record.status == "failed"
    assert record.attempts == 1
    assert record.retry_attempts == 0
    assert record.arrivals is None
    assert record.impact_score is None
    assert record.error_type == "ValueError"
    assert record.error_message == "Invalid signal state"


@pytest.mark.anyio
async def test_scheduler_start_and_stop_lifecycle() -> None:
    job_called = asyncio.Event()

    async def fake_job() -> SignalEvent:
        job_called.set()

        return make_signal()

    scheduler = PeriodicSignalScheduler(
        name=SCHEDULER_NAME,
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
        assert scheduler.status.started_at is not None
    finally:
        await scheduler.stop()

    assert scheduler.is_running is False
