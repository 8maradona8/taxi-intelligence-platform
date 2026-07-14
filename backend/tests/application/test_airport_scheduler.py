import asyncio
from datetime import timedelta
from app.application.interfaces import SchedulerRunRecord
import pytest

from app.domain.enums import (
    PriorityLevel,
    SignalSource,
    SignalType,
)
from app.domain.events import SignalEvent
from app.domain.value_objects import Confidence, ImpactScore
from app.schedulers import AirportScheduler
from app.infrastructure.http import (
    HttpResponseError,
    HttpTimeoutError,
)


@pytest.mark.anyio
async def test_scheduler_recovers_after_timeout() -> None:
    calls = 0

    async def temporary_failure_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        if calls == 1:
            raise HttpTimeoutError("Temporary airport timeout")

        return make_signal()

    scheduler = AirportScheduler(
        job=temporary_failure_job,
        interval_seconds=300,
        run_on_startup=False,
        max_attempts=2,
        retry_backoff_seconds=0,
    )

    signal = await scheduler.run_once()

    assert signal is not None
    assert calls == 2

    status = scheduler.status

    assert status.runs_total == 1
    assert status.successes_total == 1
    assert status.failures_total == 0
    assert status.retry_attempts_total == 1
    assert status.recovering is False
    assert status.last_error is None


@pytest.mark.anyio
async def test_scheduler_does_not_retry_programming_error() -> None:
    calls = 0

    async def programming_failure_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        raise ValueError("Broken mapper configuration")

    scheduler = AirportScheduler(
        job=programming_failure_job,
        interval_seconds=300,
        run_on_startup=False,
        max_attempts=3,
        retry_backoff_seconds=0,
    )

    with pytest.raises(
        ValueError,
        match="Broken mapper configuration",
    ):
        await scheduler.run_once()

    assert calls == 1

    status = scheduler.status

    assert status.failures_total == 1
    assert status.retry_attempts_total == 0


@pytest.mark.anyio
async def test_scheduler_does_not_retry_permanent_http_error() -> None:
    calls = 0

    async def permanent_failure_job() -> SignalEvent:
        nonlocal calls
        calls += 1

        raise HttpResponseError(
            status_code=404,
            message="Not Found",
        )

    scheduler = AirportScheduler(
        job=permanent_failure_job,
        interval_seconds=300,
        run_on_startup=False,
        max_attempts=3,
        retry_backoff_seconds=0,
    )

    with pytest.raises(HttpResponseError):
        await scheduler.run_once()

    assert calls == 1
    assert scheduler.status.retry_attempts_total == 0


@pytest.mark.anyio
async def test_scheduler_skips_overlapping_run() -> None:
    job_started = asyncio.Event()
    allow_completion = asyncio.Event()

    async def slow_job() -> SignalEvent:
        job_started.set()
        await allow_completion.wait()

        return make_signal()

    scheduler = AirportScheduler(
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


@pytest.mark.anyio
async def test_scheduler_records_successful_run() -> None:
    recorder = FakeSchedulerRunRecorder()

    async def successful_job() -> SignalEvent:
        return make_signal()

    scheduler = AirportScheduler(
        job=successful_job,
        interval_seconds=300,
        run_on_startup=False,
        run_recorder=recorder,
    )

    await scheduler.run_once()

    assert len(recorder.records) == 1

    record = recorder.records[0]

    assert record.scheduler_name == ("airport-signal-scheduler")
    assert record.status == "success"
    assert record.attempts == 1
    assert record.retry_attempts == 0
    assert record.impact_score == 24.0
    assert record.arrivals == 2
    assert record.error_type is None
    assert record.error_message is None
    assert record.duration_ms >= 0


@pytest.mark.anyio
async def test_scheduler_records_failed_run() -> None:
    recorder = FakeSchedulerRunRecorder()

    async def failing_job() -> SignalEvent:
        raise ValueError("Invalid airport mapper state")

    scheduler = AirportScheduler(
        job=failing_job,
        interval_seconds=300,
        run_on_startup=False,
        run_recorder=recorder,
    )

    with pytest.raises(
        ValueError,
        match="Invalid airport mapper state",
    ):
        await scheduler.run_once()

    assert len(recorder.records) == 1

    record = recorder.records[0]

    assert record.status == "failed"
    assert record.attempts == 1
    assert record.retry_attempts == 0
    assert record.impact_score is None
    assert record.arrivals is None
    assert record.error_type == "ValueError"
    assert record.error_message == ("Invalid airport mapper state")


class FakeSchedulerRunRecorder:
    def __init__(self) -> None:

        self.records: list[SchedulerRunRecord] = []

    async def record(
        self,
        run: SchedulerRunRecord,
    ) -> None:

        self.records.append(run)
