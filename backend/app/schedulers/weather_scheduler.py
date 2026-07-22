from app.application.interfaces import (
    SchedulerRunRecorder,
)
from app.schedulers.periodic_signal_scheduler import (
    PeriodicSignalScheduler,
    PeriodicSignalSchedulerStatus,
    SignalSchedulerJob,
)


WeatherJob = SignalSchedulerJob
WeatherSchedulerStatus = PeriodicSignalSchedulerStatus


class WeatherScheduler(PeriodicSignalScheduler):
    NAME = "weather-signal-scheduler"

    def __init__(
        self,
        *,
        job: WeatherJob,
        interval_seconds: float = 900.0,
        run_on_startup: bool = True,
        max_attempts: int = 2,
        retry_backoff_seconds: float = 2.0,
        run_recorder: SchedulerRunRecorder | None = None,
    ) -> None:
        super().__init__(
            name=self.NAME,
            job=job,
            interval_seconds=interval_seconds,
            run_on_startup=run_on_startup,
            max_attempts=max_attempts,
            retry_backoff_seconds=retry_backoff_seconds,
            run_recorder=run_recorder,
        )
