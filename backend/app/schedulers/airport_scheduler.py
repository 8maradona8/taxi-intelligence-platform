import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.core.logging import logger
from app.domain.events import SignalEvent


AirportJob = Callable[[], Awaitable[SignalEvent]]


@dataclass(frozen=True)
class AirportSchedulerStatus:
    name: str
    running: bool
    interval_seconds: float
    run_on_startup: bool
    started_at: datetime | None
    next_run_at: datetime | None
    last_started_at: datetime | None
    last_completed_at: datetime | None
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None
    last_impact_score: float | None
    last_arrivals: int | None
    runs_total: int
    successes_total: int
    failures_total: int


class AirportScheduler:
    NAME = "airport-signal-scheduler"

    def __init__(
        self,
        *,
        job: AirportJob,
        interval_seconds: float = 300.0,
        run_on_startup: bool = True,
    ) -> None:
        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        self._job = job
        self._interval_seconds = interval_seconds
        self._run_on_startup = run_on_startup
        self._task: asyncio.Task[None] | None = None

        self._started_at: datetime | None = None
        self._last_started_at: datetime | None = None
        self._last_completed_at: datetime | None = None
        self._last_success_at: datetime | None = None
        self._last_failure_at: datetime | None = None
        self._last_error: str | None = None
        self._last_impact_score: float | None = None
        self._last_arrivals: int | None = None

        self._runs_total = 0
        self._successes_total = 0
        self._failures_total = 0

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def status(self) -> AirportSchedulerStatus:
        next_run_at: datetime | None = None

        if self.is_running:
            if self._last_completed_at is not None:
                next_run_at = self._last_completed_at + timedelta(
                    seconds=self._interval_seconds
                )
            elif self._started_at is not None and not self._run_on_startup:
                next_run_at = self._started_at + timedelta(
                    seconds=self._interval_seconds
                )

        return AirportSchedulerStatus(
            name=self.NAME,
            running=self.is_running,
            interval_seconds=self._interval_seconds,
            run_on_startup=self._run_on_startup,
            started_at=self._started_at,
            next_run_at=next_run_at,
            last_started_at=self._last_started_at,
            last_completed_at=self._last_completed_at,
            last_success_at=self._last_success_at,
            last_failure_at=self._last_failure_at,
            last_error=self._last_error,
            last_impact_score=self._last_impact_score,
            last_arrivals=self._last_arrivals,
            runs_total=self._runs_total,
            successes_total=self._successes_total,
            failures_total=self._failures_total,
        )

    async def start(self) -> None:
        if self.is_running:
            return

        self._started_at = datetime.now(UTC)

        self._task = asyncio.create_task(
            self._run_loop(),
            name=self.NAME,
        )

        logger.info(
            "Airport scheduler started: "
            f"interval_seconds={self._interval_seconds} "
            f"run_on_startup={self._run_on_startup}"
        )

    async def stop(self) -> None:
        if self._task is None:
            return

        self._task.cancel()

        with suppress(asyncio.CancelledError):
            await self._task

        self._task = None

        logger.info("Airport scheduler stopped")

    async def run_once(self) -> SignalEvent:
        self._runs_total += 1
        self._last_started_at = datetime.now(UTC)

        try:
            signal = await self._job()
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            completed_at = datetime.now(UTC)

            self._last_completed_at = completed_at
            self._last_failure_at = completed_at
            self._last_error = f"{exc.__class__.__name__}: {exc}"
            self._failures_total += 1

            raise

        completed_at = datetime.now(UTC)

        self._last_completed_at = completed_at
        self._last_success_at = completed_at
        self._last_error = None
        self._last_impact_score = signal.impact_score.value
        self._last_arrivals = int(signal.payload.get("arrivals", 0))
        self._successes_total += 1

        logger.info(
            "Airport scheduler run completed: "
            f"zone={signal.zone_name} "
            f"impact={signal.impact_score.value} "
            f"arrivals={signal.payload.get('arrivals', 0)}"
        )

        return signal

    async def _run_loop(self) -> None:
        if self._run_on_startup:
            await self._run_safely()

        while True:
            await asyncio.sleep(self._interval_seconds)
            await self._run_safely()

    async def _run_safely(self) -> None:
        try:
            await self.run_once()
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Airport scheduler run failed")
