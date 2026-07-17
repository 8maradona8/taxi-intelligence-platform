import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from app.application.interfaces import (
    SchedulerRunRecord,
    SchedulerRunRecorder,
)
from app.core.logging import logger
from app.domain.events import SignalEvent
from app.infrastructure.http import (
    HttpRequestError,
    HttpResponseError,
    HttpTimeoutError,
)


SignalSchedulerJob = Callable[
    [],
    Awaitable[SignalEvent],
]


@dataclass(frozen=True)
class PeriodicSignalSchedulerStatus:
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
    recovering: bool = False
    max_attempts: int = 1
    current_attempt: int | None = None
    retry_backoff_seconds: float = 0.0
    retry_attempts_total: int = 0
    overlap_skips_total: int = 0


class PeriodicSignalScheduler:
    RETRYABLE_RESPONSE_STATUS_CODES = {
        429,
        500,
        502,
        503,
        504,
    }

    def __init__(
        self,
        *,
        name: str,
        job: SignalSchedulerJob,
        interval_seconds: float = 300.0,
        run_on_startup: bool = True,
        max_attempts: int = 2,
        retry_backoff_seconds: float = 2.0,
        run_recorder: SchedulerRunRecorder | None = None,
    ) -> None:
        normalized_name = name.strip()

        if not normalized_name:
            raise ValueError("scheduler name cannot be empty")

        if interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        if max_attempts <= 0:
            raise ValueError("max_attempts must be greater than zero")

        if retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds cannot be negative")

        self._name = normalized_name
        self._job = job
        self._interval_seconds = interval_seconds
        self._run_on_startup = run_on_startup
        self._max_attempts = max_attempts
        self._retry_backoff_seconds = retry_backoff_seconds
        self._run_recorder = run_recorder

        self._task: asyncio.Task[None] | None = None
        self._run_lock = asyncio.Lock()

        self._started_at: datetime | None = None
        self._last_started_at: datetime | None = None
        self._last_completed_at: datetime | None = None
        self._last_success_at: datetime | None = None
        self._last_failure_at: datetime | None = None
        self._last_error: str | None = None
        self._last_impact_score: float | None = None
        self._last_arrivals: int | None = None

        self._recovering = False
        self._current_attempt: int | None = None

        self._runs_total = 0
        self._successes_total = 0
        self._failures_total = 0
        self._retry_attempts_total = 0
        self._overlap_skips_total = 0

    @property
    def name(self) -> str:
        return self._name

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    @property
    def status(
        self,
    ) -> PeriodicSignalSchedulerStatus:
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

        return PeriodicSignalSchedulerStatus(
            name=self._name,
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
            recovering=self._recovering,
            max_attempts=self._max_attempts,
            current_attempt=self._current_attempt,
            retry_backoff_seconds=(self._retry_backoff_seconds),
            retry_attempts_total=(self._retry_attempts_total),
            overlap_skips_total=(self._overlap_skips_total),
        )

    async def start(self) -> None:
        if self.is_running:
            return

        self._started_at = datetime.now(UTC)

        self._task = asyncio.create_task(
            self._run_loop(),
            name=self._name,
        )

        logger.info(
            "Signal scheduler started: "
            f"name={self._name} "
            f"interval_seconds={self._interval_seconds} "
            f"run_on_startup={self._run_on_startup} "
            f"max_attempts={self._max_attempts}"
        )

    async def stop(self) -> None:
        if self._task is None:
            return

        self._task.cancel()

        with suppress(asyncio.CancelledError):
            await self._task

        self._task = None
        self._recovering = False
        self._current_attempt = None

        logger.info(f"Signal scheduler stopped: name={self._name}")

    async def run_once(
        self,
    ) -> SignalEvent | None:
        if self._run_lock.locked():
            self._overlap_skips_total += 1

            logger.warning(
                "Signal scheduler run skipped: "
                f"name={self._name} "
                "reason=previous execution still running"
            )

            return None

        async with self._run_lock:
            return await self._execute_with_retry()

    async def _execute_with_retry(
        self,
    ) -> SignalEvent:
        run_started_at = datetime.now(UTC)

        self._runs_total += 1
        self._last_started_at = run_started_at
        self._recovering = False

        for attempt in range(
            1,
            self._max_attempts + 1,
        ):
            self._current_attempt = attempt

            try:
                signal = await self._job()

            except asyncio.CancelledError:
                raise

            except Exception as exc:
                self._last_error = f"{exc.__class__.__name__}: {exc}"

                retryable = self._is_retryable(exc)
                has_next_attempt = attempt < self._max_attempts

                if retryable and has_next_attempt:
                    self._recovering = True
                    self._retry_attempts_total += 1

                    delay = self._retry_backoff_seconds * (2 ** (attempt - 1))

                    logger.warning(
                        "Signal scheduler temporary failure: "
                        f"name={self._name} "
                        f"attempt={attempt}/"
                        f"{self._max_attempts} "
                        f"retry_in_seconds={delay} "
                        f"error={self._last_error}"
                    )

                    await asyncio.sleep(delay)
                    continue

                completed_at = datetime.now(UTC)

                self._mark_failure(
                    exc,
                    completed_at=completed_at,
                )

                await self._record_run_safely(
                    SchedulerRunRecord(
                        scheduler_name=self._name,
                        status="failed",
                        started_at=run_started_at,
                        completed_at=completed_at,
                        duration_ms=self._duration_ms(
                            run_started_at,
                            completed_at,
                        ),
                        attempts=attempt,
                        retry_attempts=attempt - 1,
                        error_type=(exc.__class__.__name__),
                        error_message=str(exc),
                    )
                )

                raise

            completed_at = datetime.now(UTC)

            self._mark_success(
                signal,
                completed_at=completed_at,
            )

            await self._record_run_safely(
                SchedulerRunRecord(
                    scheduler_name=self._name,
                    status="success",
                    started_at=run_started_at,
                    completed_at=completed_at,
                    duration_ms=self._duration_ms(
                        run_started_at,
                        completed_at,
                    ),
                    attempts=attempt,
                    retry_attempts=attempt - 1,
                    impact_score=(signal.impact_score.value),
                    arrivals=int(
                        signal.payload.get(
                            "arrivals",
                            0,
                        )
                    ),
                )
            )

            return signal

        raise RuntimeError("Signal scheduler exhausted attempts unexpectedly")

    def _mark_success(
        self,
        signal: SignalEvent,
        *,
        completed_at: datetime,
    ) -> None:
        self._last_completed_at = completed_at
        self._last_success_at = completed_at
        self._last_error = None
        self._last_impact_score = signal.impact_score.value
        self._last_arrivals = int(
            signal.payload.get(
                "arrivals",
                0,
            )
        )

        self._successes_total += 1
        self._recovering = False
        self._current_attempt = None

        logger.info(
            "Signal scheduler run completed: "
            f"name={self._name} "
            f"zone={signal.zone_name} "
            f"impact={signal.impact_score.value} "
            f"arrivals="
            f"{signal.payload.get('arrivals', 0)}"
        )

    def _mark_failure(
        self,
        exc: Exception,
        *,
        completed_at: datetime,
    ) -> None:
        self._last_completed_at = completed_at
        self._last_failure_at = completed_at
        self._last_error = f"{exc.__class__.__name__}: {exc}"

        self._failures_total += 1
        self._recovering = False
        self._current_attempt = None

    async def _record_run_safely(
        self,
        run: SchedulerRunRecord,
    ) -> None:
        if self._run_recorder is None:
            return

        try:
            await self._run_recorder.record(run)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception(f"Failed to persist scheduler run: name={self._name}")

    @staticmethod
    def _duration_ms(
        started_at: datetime,
        completed_at: datetime,
    ) -> float:
        return round(
            (completed_at - started_at).total_seconds() * 1000,
            2,
        )

    @classmethod
    def _is_retryable(
        cls,
        exc: Exception,
    ) -> bool:
        if isinstance(
            exc,
            (
                HttpTimeoutError,
                HttpRequestError,
            ),
        ):
            return True

        if isinstance(exc, HttpResponseError):
            return exc.status_code in cls.RETRYABLE_RESPONSE_STATUS_CODES

        return False

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
            logger.exception(f"Signal scheduler run failed: name={self._name}")
