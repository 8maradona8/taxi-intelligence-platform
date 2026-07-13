from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import RequestLoggingMiddleware
from app.api.v1.airport_signals import (
    router as airport_signals_router,
)
from app.api.v1.opportunities import router as opportunities_router
from app.api.v1.recommendation import router as recommendation_router
from app.api.v1.snapshot import router as snapshot_router
from app.api.v1.system import router as system_router
from app.core.logging import logger, setup_logging
from app.core.settings import settings
from app.database.health import check_database
from app.schedulers import (
    AirportScheduler,
    collect_and_persist_airport_signal,
)
from app.shared.errors import register_exception_handlers

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

    airport_scheduler: AirportScheduler | None = None
    app.state.airport_scheduler = None

    if settings.airport_scheduler_enabled and database_ok:
        airport_scheduler = AirportScheduler(
            job=collect_and_persist_airport_signal,
            interval_seconds=(settings.airport_scheduler_interval_seconds),
            run_on_startup=(settings.airport_scheduler_run_on_startup),
        )

        await airport_scheduler.start()
        app.state.airport_scheduler = airport_scheduler
    elif not settings.airport_scheduler_enabled:
        logger.info("Airport scheduler is disabled")
    else:
        logger.warning(
            "Airport scheduler was not started because PostgreSQL is unavailable"
        )

    logger.info("Backend is ready.")

    try:
        yield
    finally:
        if airport_scheduler is not None:
            await airport_scheduler.stop()

        app.state.airport_scheduler = None

        logger.info("=" * 60)
        logger.info("Stopping Taxi Intelligence Platform")
        logger.info("=" * 60)


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)

register_exception_handlers(app)

app.include_router(
    airport_signals_router,
    prefix="/api/v1",
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

app.include_router(
    system_router,
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
        "status": ("healthy" if database_ok else "unhealthy"),
        "database": database_ok,
        "environment": settings.environment,
    }
