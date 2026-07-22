from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.middleware import RequestLoggingMiddleware
from app.api.v1.airport_signals import (
    router as airport_signals_router,
)
from app.api.v1.opportunities import (
    router as opportunities_router,
)
from app.api.v1.recommendation import (
    router as recommendation_router,
)
from app.api.v1.snapshot import router as snapshot_router
from app.api.v1.system import router as system_router
from app.application.interfaces import (
    AIRPORT_SCHEDULER,
    BUS_SCHEDULER,
    RAILWAY_SCHEDULER,
    WEATHER_SCHEDULER,
)
from app.core.logging import logger, setup_logging
from app.core.settings import settings
from app.database.health import check_database
from app.database.session import AsyncSessionLocal
from app.schedulers import (
    AirportScheduler,
    BusScheduler,
    RailwayScheduler,
    SchedulerRegistry,
    WeatherScheduler,
    collect_and_persist_airport_signal,
    collect_and_persist_bus_signal,
    collect_and_persist_railway_signal,
    collect_and_persist_weather_signal,
)
from app.services.postgres_scheduler_run_recorder import (
    PostgresSchedulerRunRecorder,
)
from app.shared.errors import (
    register_exception_handlers,
)

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

    scheduler_registry = SchedulerRegistry()

    scheduler_registry.register(
        identity=AIRPORT_SCHEDULER,
        enabled=settings.airport_scheduler_enabled,
    )
    scheduler_registry.register(
        identity=BUS_SCHEDULER,
        enabled=settings.bus_scheduler_enabled,
    )
    scheduler_registry.register(
        identity=RAILWAY_SCHEDULER,
        enabled=settings.railway_scheduler_enabled,
    )
    scheduler_registry.register(
        identity=WEATHER_SCHEDULER,
        enabled=settings.weather_scheduler_enabled,
    )

    app.state.scheduler_registry = scheduler_registry
    app.state.airport_scheduler = None
    app.state.bus_scheduler = None
    app.state.railway_scheduler = None
    app.state.weather_scheduler = None

    run_recorder = PostgresSchedulerRunRecorder(
        session_factory=AsyncSessionLocal,
    )

    airport_scheduler: AirportScheduler | None = None
    bus_scheduler: BusScheduler | None = None
    railway_scheduler: RailwayScheduler | None = None
    weather_scheduler: WeatherScheduler | None = None

    if settings.airport_scheduler_enabled and database_ok:
        airport_scheduler = AirportScheduler(
            job=collect_and_persist_airport_signal,
            interval_seconds=(settings.airport_scheduler_interval_seconds),
            run_on_startup=(settings.airport_scheduler_run_on_startup),
            max_attempts=(settings.airport_scheduler_max_attempts),
            retry_backoff_seconds=(settings.airport_scheduler_retry_backoff_seconds),
            run_recorder=run_recorder,
        )

        await airport_scheduler.start()

        scheduler_registry.attach_runtime(
            scheduler_key=AIRPORT_SCHEDULER.key,
            runtime=airport_scheduler,
        )

        app.state.airport_scheduler = airport_scheduler

    elif not settings.airport_scheduler_enabled:
        logger.info("Airport scheduler is disabled")
    else:
        logger.warning(
            "Airport scheduler was not started because PostgreSQL is unavailable"
        )

    if settings.bus_scheduler_enabled and database_ok:
        bus_scheduler = BusScheduler(
            job=collect_and_persist_bus_signal,
            interval_seconds=(settings.bus_scheduler_interval_seconds),
            run_on_startup=(settings.bus_scheduler_run_on_startup),
            max_attempts=settings.bus_scheduler_max_attempts,
            retry_backoff_seconds=(settings.bus_scheduler_retry_backoff_seconds),
            run_recorder=run_recorder,
        )

        await bus_scheduler.start()

        scheduler_registry.attach_runtime(
            scheduler_key=BUS_SCHEDULER.key,
            runtime=bus_scheduler,
        )

        app.state.bus_scheduler = bus_scheduler

    elif not settings.bus_scheduler_enabled:
        logger.info("Bus scheduler is disabled")
    else:
        logger.warning(
            "Bus scheduler was not started because PostgreSQL is unavailable"
        )

    if settings.railway_scheduler_enabled and database_ok:
        railway_scheduler = RailwayScheduler(
            job=collect_and_persist_railway_signal,
            interval_seconds=(settings.railway_scheduler_interval_seconds),
            run_on_startup=(settings.railway_scheduler_run_on_startup),
            max_attempts=(settings.railway_scheduler_max_attempts),
            retry_backoff_seconds=(settings.railway_scheduler_retry_backoff_seconds),
            run_recorder=run_recorder,
        )

        await railway_scheduler.start()

        scheduler_registry.attach_runtime(
            scheduler_key=RAILWAY_SCHEDULER.key,
            runtime=railway_scheduler,
        )

        app.state.railway_scheduler = railway_scheduler

    elif not settings.railway_scheduler_enabled:
        logger.info("Railway scheduler is disabled")
    else:
        logger.warning(
            "Railway scheduler was not started because PostgreSQL is unavailable"
        )

    if settings.weather_scheduler_enabled and database_ok:
        weather_scheduler = WeatherScheduler(
            job=collect_and_persist_weather_signal,
            interval_seconds=(settings.weather_scheduler_interval_seconds),
            run_on_startup=(settings.weather_scheduler_run_on_startup),
            max_attempts=(settings.weather_scheduler_max_attempts),
            retry_backoff_seconds=(settings.weather_scheduler_retry_backoff_seconds),
            run_recorder=run_recorder,
        )

        await weather_scheduler.start()

        scheduler_registry.attach_runtime(
            scheduler_key=WEATHER_SCHEDULER.key,
            runtime=weather_scheduler,
        )

        app.state.weather_scheduler = weather_scheduler

    elif not settings.weather_scheduler_enabled:
        logger.info("Weather scheduler is disabled")
    else:
        logger.warning(
            "Weather scheduler was not started because PostgreSQL is unavailable"
        )

    logger.info("Backend is ready.")

    try:
        yield
    finally:
        if weather_scheduler is not None:
            await weather_scheduler.stop()

        if railway_scheduler is not None:
            await railway_scheduler.stop()

        if bus_scheduler is not None:
            await bus_scheduler.stop()

        if airport_scheduler is not None:
            await airport_scheduler.stop()

        scheduler_registry.detach_runtime(WEATHER_SCHEDULER.key)
        scheduler_registry.detach_runtime(RAILWAY_SCHEDULER.key)
        scheduler_registry.detach_runtime(BUS_SCHEDULER.key)
        scheduler_registry.detach_runtime(AIRPORT_SCHEDULER.key)

        app.state.weather_scheduler = None
        app.state.railway_scheduler = None
        app.state.bus_scheduler = None
        app.state.airport_scheduler = None
        app.state.scheduler_registry = None

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
        "environment": settings.environment.value,
        "status": "running",
    }


@app.get("/health")
async def health():
    database_ok = await check_database()

    return {
        "status": ("healthy" if database_ok else "unhealthy"),
        "database": database_ok,
        "environment": settings.environment.value,
    }
