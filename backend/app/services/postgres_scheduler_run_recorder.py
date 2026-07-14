from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
)

from app.application.interfaces import SchedulerRunRecord
from app.repositories import SchedulerRunRepository


class PostgresSchedulerRunRecorder:
    def __init__(
        self,
        *,
        session_factory: async_sessionmaker[AsyncSession],
    ) -> None:
        self._session_factory = session_factory

    async def record(
        self,
        run: SchedulerRunRecord,
    ) -> None:
        async with self._session_factory() as session:
            repository = SchedulerRunRepository(session)

            await repository.create(run)
