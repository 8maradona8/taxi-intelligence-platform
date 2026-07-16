from typing import cast

from fastapi import Depends, HTTPException, Request, status

from app.application.interfaces import AIRPORT_SCHEDULER
from app.schedulers import (
    AirportScheduler,
    SchedulerRegistration,
    SchedulerRegistry,
)


def get_scheduler_registry(
    request: Request,
) -> SchedulerRegistry:
    registry = getattr(
        request.app.state,
        "scheduler_registry",
        None,
    )

    if registry is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Scheduler registry is unavailable.",
        )

    return cast(SchedulerRegistry, registry)


def get_scheduler_registration(
    scheduler_key: str,
    registry: SchedulerRegistry = Depends(get_scheduler_registry),
) -> SchedulerRegistration:
    try:
        return registry.get(scheduler_key)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=(f"Unknown scheduler: {scheduler_key}"),
        ) from exc


def get_airport_scheduler(
    request: Request,
) -> AirportScheduler | None:
    legacy_scheduler = getattr(
        request.app.state,
        "airport_scheduler",
        None,
    )

    if legacy_scheduler is not None:
        return cast(
            AirportScheduler,
            legacy_scheduler,
        )

    registry = getattr(
        request.app.state,
        "scheduler_registry",
        None,
    )

    if registry is None:
        return None

    try:
        runtime = registry.get_runtime(AIRPORT_SCHEDULER.key)
    except KeyError:
        return None

    return cast(
        AirportScheduler | None,
        runtime,
    )
