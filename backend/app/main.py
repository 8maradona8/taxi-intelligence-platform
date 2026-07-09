from contextlib import asynccontextmanager

from fastapi import FastAPI
from app.api.v1.recommendation import router as recommendation_router
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.snapshot import router as snapshot_router
from app.core.logging import logger, setup_logging
from app.core.settings import settings
from app.database.health import check_database

setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("=" * 60)
    logger.info("Starting Taxi Intelligence Platform")
    logger.info("=" * 60)

    database_ok = await check_database()

    if database_ok:
        logger.info("✓ PostgreSQL connection established")
    else:
        logger.error("✗ PostgreSQL connection failed")

    logger.info("Backend is ready.")

    yield

    logger.info("=" * 60)
    logger.info("Stopping Taxi Intelligence Platform")
    logger.info("=" * 60)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.include_router(
    snapshot_router,
    prefix="/api/v1",
)

app.include_router(
    opportunities_router,
    prefix="/api/v1",
)

app.include_router(
    recommendation_router,
    prefix="/api/v1",
)

@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "running",
    }


@app.get("/health")
async def health():
    database_ok = await check_database()

    return {
        "status": "healthy" if database_ok else "unhealthy",
        "database": database_ok,
        "environment": settings.environment,
    }