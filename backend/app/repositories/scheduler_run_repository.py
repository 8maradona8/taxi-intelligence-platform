from datetime import datetime

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces import (
    SchedulerFailureBreakdown,
    SchedulerFailureGroup,
    SchedulerMetricsWindow,
    SchedulerRunMetrics,
    SchedulerRunRecord,
)
from app.models.scheduler_run import SchedulerRun


class SchedulerRunRepository:
    def __init__(
        self,
        session: AsyncSession,
    ) -> None:
        self._session = session

    async def create(
        self,
        run: SchedulerRunRecord,
    ) -> SchedulerRun:
        scheduler_run = SchedulerRun(
            scheduler_name=run.scheduler_name,
            status=run.status,
            started_at=run.started_at,
            completed_at=run.completed_at,
            duration_ms=run.duration_ms,
            attempts=run.attempts,
            retry_attempts=run.retry_attempts,
            impact_score=run.impact_score,
            arrivals=run.arrivals,
            error_type=run.error_type,
            error_message=run.error_message,
        )

        self._session.add(scheduler_run)

        await self._session.commit()
        await self._session.refresh(scheduler_run)

        return scheduler_run

    async def list_latest(
        self,
        *,
        scheduler_name: str,
        limit: int = 20,
    ) -> list[SchedulerRun]:
        result = await self._session.execute(
            select(SchedulerRun)
            .where(SchedulerRun.scheduler_name == scheduler_name)
            .order_by(SchedulerRun.started_at.desc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def get_metrics(
        self,
        *,
        scheduler_name: str,
        window: SchedulerMetricsWindow,
        window_started_at: datetime | None,
        window_ended_at: datetime,
    ) -> SchedulerRunMetrics:
        statement = select(
            func.count(SchedulerRun.id).label("total_runs"),
            func.sum(
                case(
                    (
                        SchedulerRun.status == "success",
                        1,
                    ),
                    else_=0,
                )
            ).label("successful_runs"),
            func.sum(
                case(
                    (
                        SchedulerRun.status == "failed",
                        1,
                    ),
                    else_=0,
                )
            ).label("failed_runs"),
            func.avg(SchedulerRun.duration_ms).label("average_duration_ms"),
            func.avg(SchedulerRun.attempts).label("average_attempts"),
            func.coalesce(
                func.sum(SchedulerRun.retry_attempts),
                0,
            ).label("total_retry_attempts"),
            func.max(SchedulerRun.completed_at).label("last_run_at"),
            func.max(
                case(
                    (
                        SchedulerRun.status == "success",
                        SchedulerRun.completed_at,
                    ),
                    else_=None,
                )
            ).label("last_success_at"),
            func.max(
                case(
                    (
                        SchedulerRun.status == "failed",
                        SchedulerRun.completed_at,
                    ),
                    else_=None,
                )
            ).label("last_failure_at"),
        ).where(
            SchedulerRun.scheduler_name == scheduler_name,
            SchedulerRun.completed_at <= window_ended_at,
        )

        if window_started_at is not None:
            statement = statement.where(SchedulerRun.completed_at >= window_started_at)

        result = await self._session.execute(statement)
        row = result.one()

        return SchedulerRunMetrics(
            scheduler_name=scheduler_name,
            window=window,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
            total_runs=int(row.total_runs or 0),
            successful_runs=int(row.successful_runs or 0),
            failed_runs=int(row.failed_runs or 0),
            average_duration_ms=round(
                float(row.average_duration_ms or 0),
                2,
            ),
            average_attempts=round(
                float(row.average_attempts or 0),
                2,
            ),
            total_retry_attempts=int(row.total_retry_attempts or 0),
            last_run_at=row.last_run_at,
            last_success_at=row.last_success_at,
            last_failure_at=row.last_failure_at,
        )

    async def get_failure_breakdown(
        self,
        *,
        scheduler_name: str,
        window: SchedulerMetricsWindow,
        window_started_at: datetime | None,
        window_ended_at: datetime,
    ) -> SchedulerFailureBreakdown:
        filters = [
            SchedulerRun.scheduler_name == scheduler_name,
            SchedulerRun.status == "failed",
            SchedulerRun.completed_at <= window_ended_at,
        ]

        if window_started_at is not None:
            filters.append(SchedulerRun.completed_at >= window_started_at)

        total_result = await self._session.execute(
            select(func.count(SchedulerRun.id)).where(*filters)
        )

        total_failures = int(total_result.scalar_one() or 0)

        error_type_expression = func.coalesce(
            SchedulerRun.error_type,
            "UnknownError",
        )

        grouped_result = await self._session.execute(
            select(
                error_type_expression.label("error_type"),
                func.count(SchedulerRun.id).label("failure_count"),
                func.max(SchedulerRun.completed_at).label("last_occurred_at"),
            )
            .where(*filters)
            .group_by(error_type_expression)
            .order_by(
                func.count(SchedulerRun.id).desc(),
                func.max(SchedulerRun.completed_at).desc(),
            )
        )

        groups: list[SchedulerFailureGroup] = []

        for row in grouped_result.all():
            latest_message_result = await self._session.execute(
                select(SchedulerRun.error_message)
                .where(
                    *filters,
                    error_type_expression == row.error_type,
                )
                .order_by(SchedulerRun.completed_at.desc())
                .limit(1)
            )

            groups.append(
                SchedulerFailureGroup(
                    error_type=str(row.error_type),
                    count=int(row.failure_count),
                    last_occurred_at=row.last_occurred_at,
                    latest_message=(latest_message_result.scalar_one_or_none()),
                )
            )

        return SchedulerFailureBreakdown(
            scheduler_name=scheduler_name,
            window=window,
            window_started_at=window_started_at,
            window_ended_at=window_ended_at,
            total_failures=total_failures,
            failures=groups,
        )
