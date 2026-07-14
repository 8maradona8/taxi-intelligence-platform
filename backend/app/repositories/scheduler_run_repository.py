from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces import (
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
        ).where(SchedulerRun.scheduler_name == scheduler_name)

        result = await self._session.execute(statement)

        row = result.one()

        return SchedulerRunMetrics(
            scheduler_name=scheduler_name,
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
