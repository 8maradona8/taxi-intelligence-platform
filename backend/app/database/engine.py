from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    create_async_engine,
)

from app.core.settings import settings


engine: AsyncEngine = create_async_engine(
    settings.database_url,
    echo=settings.environment == "development",
    pool_pre_ping=True,
    pool_recycle=3600,
)