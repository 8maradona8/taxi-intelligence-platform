from dataclasses import dataclass
from datetime import datetime

from app.services.scheduler_health_service import SchedulerHealth


@dataclass(frozen=True)
class DatabaseHealthResponse:
    status: str
    connected: bool


@dataclass(frozen=True)
class SchedulerHealthResponse:
    status: str
    enabled: bool
    initialized: bool
    running: bool
    stale: bool
    message: str
    last_success_at: datetime | None
    last_failure_at: datetime | None
    last_error: str | None
    runs_total: int
    successes_total: int
    failures_total: int

    @classmethod
    def from_health(
        cls,
        health: SchedulerHealth,
    ) -> "SchedulerHealthResponse":
        return cls(
            status=health.status,
            enabled=health.enabled,
            initialized=health.initialized,
            running=health.running,
            stale=health.stale,
            message=health.message,
            last_success_at=health.last_success_at,
            last_failure_at=health.last_failure_at,
            last_error=health.last_error,
            runs_total=health.runs_total,
            successes_total=health.successes_total,
            failures_total=health.failures_total,
        )


@dataclass(frozen=True)
class SystemHealthResponse:
    status: str
    service: str
    version: str
    environment: str
    database: DatabaseHealthResponse
    airport_scheduler: SchedulerHealthResponse
