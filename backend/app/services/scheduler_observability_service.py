from datetime import UTC, datetime

from app.application.interfaces import (
    SchedulerMetricsWindow,
    SchedulerObservabilityOverview,
    SchedulerRuntime,
    SchedulerTrendGranularity,
)
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)


class SchedulerObservabilityService:
    def __init__(
        self,
        *,
        history_service: SchedulerRunHistoryService,
    ) -> None:
        self._history_service = history_service

    async def get_overview(
        self,
        *,
        scheduler: SchedulerRuntime | None,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        granularity: (SchedulerTrendGranularity | None) = None,
        now: datetime | None = None,
    ) -> SchedulerObservabilityOverview:
        observed_at = self._normalize_now(now)

        metrics = await self._history_service.get_metrics(
            window=window,
            now=observed_at,
        )

        failure_breakdown = await self._history_service.get_failure_breakdown(
            window=window,
            now=observed_at,
        )

        reliability_trend = await self._history_service.get_reliability_trend(
            window=window,
            granularity=granularity,
            now=observed_at,
        )

        scheduler_status = scheduler.status if scheduler is not None else None

        return SchedulerObservabilityOverview(
            observed_at=observed_at,
            scheduler_status=scheduler_status,
            metrics=metrics,
            failure_breakdown=(failure_breakdown),
            reliability_trend=(reliability_trend),
        )

    async def get_airport_overview(
        self,
        *,
        scheduler: SchedulerRuntime | None,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        granularity: (SchedulerTrendGranularity | None) = None,
        now: datetime | None = None,
    ) -> SchedulerObservabilityOverview:
        return await self.get_overview(
            scheduler=scheduler,
            window=window,
            granularity=granularity,
            now=now,
        )

    @staticmethod
    def _normalize_now(
        value: datetime | None,
    ) -> datetime:
        normalized = value or datetime.now(UTC)

        if normalized.tzinfo is None:
            return normalized.replace(tzinfo=UTC)

        return normalized
