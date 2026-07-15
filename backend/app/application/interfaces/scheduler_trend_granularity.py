from enum import StrEnum

from app.application.interfaces.scheduler_metrics_window import (
    SchedulerMetricsWindow,
)


class SchedulerTrendGranularity(StrEnum):
    HOUR = "hour"
    DAY = "day"

    @classmethod
    def default_for_window(
        cls,
        window: SchedulerMetricsWindow,
    ) -> "SchedulerTrendGranularity":
        if window == SchedulerMetricsWindow.HOURS_24:
            return cls.HOUR

        return cls.DAY
