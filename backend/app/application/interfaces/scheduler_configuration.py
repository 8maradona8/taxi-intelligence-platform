from dataclasses import dataclass

from app.application.interfaces.scheduler_identity import (
    SchedulerIdentity,
)


@dataclass(frozen=True)
class SchedulerConfiguration:
    identity: SchedulerIdentity
    enabled: bool
    interval_seconds: float
    run_on_startup: bool
    max_attempts: int
    retry_backoff_seconds: float

    def __post_init__(self) -> None:
        if self.interval_seconds <= 0:
            raise ValueError("interval_seconds must be greater than zero")

        if self.max_attempts <= 0:
            raise ValueError("max_attempts must be greater than zero")

        if self.retry_backoff_seconds < 0:
            raise ValueError("retry_backoff_seconds cannot be negative")
