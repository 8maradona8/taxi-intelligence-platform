from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.dependencies import get_airport_scheduler
from app.application.dto import SchedulerStatusResponse
from app.core.settings import settings
from app.database.health import check_database
from app.schedulers import AirportScheduler


router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/health")
async def system_health():
    database_ok = await check_database()

    return {
        "status": ("healthy" if database_ok else "unhealthy"),
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": {
            "status": ("connected" if database_ok else "disconnected"),
        },
    }


@router.get("/schedulers/airport")
async def airport_scheduler_status(
    scheduler: AirportScheduler | None = Depends(get_airport_scheduler),
):
    if scheduler is None:
        response = SchedulerStatusResponse.unavailable(
            enabled=settings.airport_scheduler_enabled,
            interval_seconds=(settings.airport_scheduler_interval_seconds),
            run_on_startup=(settings.airport_scheduler_run_on_startup),
        )
    else:
        response = SchedulerStatusResponse.from_status(scheduler.status)

    return asdict(response)
