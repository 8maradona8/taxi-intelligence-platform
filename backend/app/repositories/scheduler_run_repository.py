from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.application.interfaces import SchedulerRunRecord
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
