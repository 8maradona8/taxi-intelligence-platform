from datetime import UTC, datetime

from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerIdentity,
    SchedulerMetricsWindow,
    SchedulerReliabilityTrend,
    SchedulerRunMetrics,
    SchedulerTrendGranularity,
)
from app.models.scheduler_run import SchedulerRun
from app.repositories import SchedulerRunRepository


class SchedulerRunHistoryService:
    def __init__(
        self,
        *,
        repository: SchedulerRunRepository,
        scheduler_identity: SchedulerIdentity,
    ) -> None:
        self._repository = repository
        self._scheduler_identity = scheduler_identity

    @property
    def scheduler_identity(
        self,
    ) -> SchedulerIdentity:
        return self._scheduler_identity

    async def get_runs(
        self,
        *,
        limit: int = 20,
    ) -> list[SchedulerRun]:
        return await self._repository.list_latest(
            scheduler_name=self._scheduler_identity.name,
            limit=limit,
        )

    async def get_metrics(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        now: datetime | None = None,
    ) -> SchedulerRunMetrics:
        window_ended_at = self._normalize_now(now)

        window_started_at = window.started_at(ended_at=window_ended_at)

        return await self._repository.get_metrics(
            scheduler_name=self._scheduler_identity.name,
            window=window,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
        )

    async def get_failure_breakdown(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        now: datetime | None = None,
    ) -> SchedulerFailureBreakdown:
        window_ended_at = self._normalize_now(now)

        window_started_at = window.started_at(ended_at=window_ended_at)

        return await self._repository.get_failure_breakdown(
            scheduler_name=self._scheduler_identity.name,
            window=window,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
        )

    async def get_reliability_trend(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        granularity: (SchedulerTrendGranularity | None) = None,
        now: datetime | None = None,
    ) -> SchedulerReliabilityTrend:
        window_ended_at = self._normalize_now(now)

        window_started_at = window.started_at(ended_at=window_ended_at)

        resolved_granularity = (
            granularity or SchedulerTrendGranularity.default_for_window(window)
        )

        return await self._repository.get_reliability_trend(
            scheduler_name=self._scheduler_identity.name,
            window=window,
            granularity=resolved_granularity,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
        )

    async def get_airport_runs(
        self,
        *,
        limit: int = 20,
    ) -> list[SchedulerRun]:
        return await self.get_runs(
            limit=limit,
        )

    async def get_airport_metrics(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        now: datetime | None = None,
    ) -> SchedulerRunMetrics:
        return await self.get_metrics(
            window=window,
            now=now,
        )

    async def get_airport_failure_breakdown(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        now: datetime | None = None,
    ) -> SchedulerFailureBreakdown:
        return await self.get_failure_breakdown(
            window=window,
            now=now,
        )

    async def get_airport_reliability_trend(
        self,
        *,
        window: SchedulerMetricsWindow = (SchedulerMetricsWindow.HOURS_24),
        granularity: (SchedulerTrendGranularity | None) = None,
        now: datetime | None = None,
    ) -> SchedulerReliabilityTrend:
        return await self.get_reliability_trend(
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
