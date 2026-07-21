from dataclasses import asdict

from fastapi import APIRouter, Depends, Query
from app.services.scheduler_observability_service import (
    SchedulerObservabilityService,
)
from app.api.dependencies import (
    get_airport_scheduler,
    get_scheduler_configuration,
    get_scheduler_registry,
    get_scheduler_run_history_service,
    get_scheduler_runtime,
)
from app.application.dto import (
    DatabaseHealthResponse,
    SchedulerFailureBreakdownResponse,
    SchedulerHealthResponse,
    SchedulerRunHistoryResponse,
    SchedulerRunMetricsResponse,
    SchedulerStatusResponse,
    SystemHealthResponse,
    SchedulerReliabilityTrendResponse,
    SchedulerObservabilityOverviewResponse,
    SchedulerRegistryResponse,
)
from app.core.settings import settings
from app.database.health import check_database
from app.schedulers import (
    AirportScheduler,
    SchedulerRegistry,
)
from app.services.scheduler_health_service import (
    SchedulerHealthService,
)
from app.services.scheduler_run_history_service import (
    SchedulerRunHistoryService,
)
from app.application.interfaces import (
    SchedulerConfiguration,
    SchedulerMetricsWindow,
    SchedulerRuntime,
    SchedulerTrendGranularity,
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


@router.get("/schedulers")
async def scheduler_registry_metadata(
    registry: SchedulerRegistry = Depends(get_scheduler_registry),
):
    response = SchedulerRegistryResponse.from_registrations(registry.list_all())

    return asdict(response)


@router.get("/schedulers/{scheduler_key}")
async def scheduler_status(
    configuration: SchedulerConfiguration = Depends(
        get_scheduler_configuration,
    ),
    scheduler: SchedulerRuntime | None = Depends(
        get_scheduler_runtime,
    ),
):
    if scheduler is None:
        response = SchedulerStatusResponse.unavailable(
            name=configuration.identity.name,
            enabled=configuration.enabled,
            interval_seconds=configuration.interval_seconds,
            run_on_startup=configuration.run_on_startup,
            max_attempts=configuration.max_attempts,
            retry_backoff_seconds=configuration.retry_backoff_seconds,
        )
    else:
        response = SchedulerStatusResponse.from_status(scheduler.status)

    return asdict(response)


@router.get("/schedulers/{scheduler_key}/runs")
async def scheduler_run_history(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    service: SchedulerRunHistoryService = Depends(get_scheduler_run_history_service),
):
    runs = await service.get_runs(limit=limit)

    response = SchedulerRunHistoryResponse.from_models(
        scheduler_name=(service.scheduler_identity.name),
        runs=runs,
    )

    return asdict(response)


@router.get("/schedulers/{scheduler_key}/metrics")
async def scheduler_run_metrics(
    window: SchedulerMetricsWindow = Query(
        default=(SchedulerMetricsWindow.HOURS_24),
    ),
    service: SchedulerRunHistoryService = Depends(get_scheduler_run_history_service),
):
    metrics = await service.get_metrics(window=window)

    response = SchedulerRunMetricsResponse.from_metrics(metrics)

    return asdict(response)


@router.get("/schedulers/{scheduler_key}/failures")
async def scheduler_failure_breakdown(
    window: SchedulerMetricsWindow = Query(
        default=(SchedulerMetricsWindow.HOURS_24),
    ),
    service: SchedulerRunHistoryService = Depends(get_scheduler_run_history_service),
):
    breakdown = await service.get_failure_breakdown(window=window)

    response = SchedulerFailureBreakdownResponse.from_breakdown(breakdown)

    return asdict(response)


@router.get("/schedulers/{scheduler_key}/trends")
async def scheduler_reliability_trend(
    window: SchedulerMetricsWindow = Query(
        default=(SchedulerMetricsWindow.HOURS_24),
    ),
    granularity: (SchedulerTrendGranularity | None) = Query(default=None),
    service: SchedulerRunHistoryService = Depends(get_scheduler_run_history_service),
):
    trend = await service.get_reliability_trend(
        window=window,
        granularity=granularity,
    )

    response = SchedulerReliabilityTrendResponse.from_trend(trend)

    return asdict(response)


@router.get("/schedulers/{scheduler_key}/overview")
async def scheduler_observability_overview(
    window: SchedulerMetricsWindow = Query(
        default=(SchedulerMetricsWindow.HOURS_24),
    ),
    granularity: (SchedulerTrendGranularity | None) = Query(default=None),
    configuration: SchedulerConfiguration = Depends(get_scheduler_configuration),
    scheduler: SchedulerRuntime | None = Depends(get_scheduler_runtime),
    history_service: SchedulerRunHistoryService = Depends(
        get_scheduler_run_history_service
    ),
):
    service = SchedulerObservabilityService(
        history_service=history_service,
    )

    overview = await service.get_overview(
        scheduler=scheduler,
        window=window,
        granularity=granularity,
    )

    response = SchedulerObservabilityOverviewResponse.from_overview(
        overview,
        scheduler_name=(configuration.identity.name),
        scheduler_enabled=(configuration.enabled),
        interval_seconds=(configuration.interval_seconds),
        run_on_startup=(configuration.run_on_startup),
        max_attempts=(configuration.max_attempts),
        retry_backoff_seconds=(configuration.retry_backoff_seconds),
    )

    return asdict(response)
