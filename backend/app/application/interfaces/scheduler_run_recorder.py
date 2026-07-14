from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class SchedulerRunRecord:
    scheduler_name: str
    status: str
    started_at: datetime
    completed_at: datetime
    duration_ms: float
    attempts: int
    retry_attempts: int
    impact_score: float | None = None
    arrivals: int | None = None
    error_type: str | None = None
    error_message: str | None = None


class SchedulerRunRecorder(Protocol):
    async def record(
        self,
        run: SchedulerRunRecord,
    ) -> None:
        """Persist one completed scheduler run."""
