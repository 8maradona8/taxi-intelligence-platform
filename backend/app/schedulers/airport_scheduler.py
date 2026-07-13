import asyncio
from collections.abc import Awaitable, Callable
from contextlib import suppress

from app.core.logging import logger
from app.domain.events import SignalEvent


AirportJob = Callable[[], Awaitable[SignalEvent]]


class AirportScheduler:
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

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def start(self) -> None:
        if self.is_running:
            return

        self._task = asyncio.create_task(
            self._run_loop(),
            name="airport-signal-scheduler",
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
        signal = await self._job()

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
