from datetime import datetime, timedelta
from enum import StrEnum


class SchedulerMetricsWindow(StrEnum):
    HOURS_24 = "24h"
    DAYS_7 = "7d"
    DAYS_30 = "30d"
    ALL = "all"

    def started_at(
        self,
        *,
        ended_at: datetime,
    ) -> datetime | None:
        durations = {
            SchedulerMetricsWindow.HOURS_24: timedelta(hours=24),
            SchedulerMetricsWindow.DAYS_7: timedelta(days=7),
            SchedulerMetricsWindow.DAYS_30: timedelta(days=30),
        }

        duration = durations.get(self)

        if duration is None:
            return None

        return ended_at - duration
