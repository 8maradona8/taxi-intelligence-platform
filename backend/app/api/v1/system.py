from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_airport_scheduler,
    get_scheduler_run_history_service,
)
from app.application.dto import (
    DatabaseHealthResponse,
    SchedulerHealthResponse,
    SchedulerRunHistoryResponse,
    SchedulerRunMetricsResponse,
    SchedulerStatusResponse,
    SystemHealthResponse,
)
from app.core.settings import settings
from app.database.health import check_database
from app.schedulers import AirportScheduler
from app.services.scheduler_health_service import (
    SchedulerHealthService,
)
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)
from app.application.interfaces import (
    SchedulerMetricsWindow,
)

router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/health")
async def system_health(
    scheduler: AirportScheduler | None = Depends(get_airport_scheduler),
):
    database_ok = await check_database()

    scheduler_status = scheduler.status if scheduler is not None else None

    scheduler_health = SchedulerHealthService().evaluate(
        enabled=settings.airport_scheduler_enabled,
        scheduler_status=scheduler_status,
    )

    if not database_ok:
        overall_status = "unhealthy"
    elif scheduler_health.status in {
        "unhealthy",
        "degraded",
        "recovering",
    }:
        overall_status = (
            "degraded"
            if scheduler_health.status == "recovering"
            else scheduler_health.status
        )
    else:
        overall_status = "healthy"

    response = SystemHealthResponse(
        status=overall_status,
        service=settings.app_name,
        version=settings.app_version,
        environment=settings.environment.value,
        database=DatabaseHealthResponse(
            status=("connected" if database_ok else "disconnected"),
            connected=database_ok,
        ),
        airport_scheduler=SchedulerHealthResponse.from_health(scheduler_health),
    )

    return asdict(response)


@router.get("/schedulers/airport")
async def airport_scheduler_status(
    scheduler: AirportScheduler | None = Depends(get_airport_scheduler),
):
    if scheduler is None:
        response = SchedulerStatusResponse.unavailable(
            enabled=settings.airport_scheduler_enabled,
            interval_seconds=(settings.airport_scheduler_interval_seconds),
            run_on_startup=(settings.airport_scheduler_run_on_startup),
            max_attempts=(settings.airport_scheduler_max_attempts),
            retry_backoff_seconds=(settings.airport_scheduler_retry_backoff_seconds),
        )
    else:
        response = SchedulerStatusResponse.from_status(scheduler.status)

    return asdict(response)


@router.get("/schedulers/airport/runs")
async def airport_scheduler_run_history(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    service: SchedulerRunHistoryService = Depends(get_scheduler_run_history_service),
):
    runs = await service.get_airport_runs(
        limit=limit,
    )

    response = SchedulerRunHistoryResponse.from_models(
        scheduler_name=AirportScheduler.NAME,
        runs=runs,
    )

    return asdict(response)


@router.get("/schedulers/airport/metrics")
async def airport_scheduler_run_metrics(
    window: SchedulerMetricsWindow = Query(
        default=SchedulerMetricsWindow.HOURS_24,
    ),
    service: SchedulerRunHistoryService = Depends(get_scheduler_run_history_service),
):
    metrics = await service.get_airport_metrics(
        window=window,
    )

    response = SchedulerRunMetricsResponse.from_metrics(metrics)

    return asdict(response)
