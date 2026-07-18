from typing import cast

from fastapi import Depends, HTTPException, Request, status

from app.application.interfaces import (
    AIRPORT_SCHEDULER,
    RAILWAY_SCHEDULER,
    SchedulerConfiguration,
    SchedulerIdentity,
    SchedulerRuntime,
)
from app.core.settings import settings
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
            detail=f"Unknown scheduler: {scheduler_key}",
        ) from exc


def get_scheduler_identity(
    registration: SchedulerRegistration = Depends(get_scheduler_registration),
) -> SchedulerIdentity:
    return registration.identity


def get_scheduler_runtime(
    request: Request,
    scheduler_key: str,
) -> SchedulerRuntime | None:
    if scheduler_key == AIRPORT_SCHEDULER.key:
        legacy_scheduler = getattr(
            request.app.state,
            "airport_scheduler",
            None,
        )

        if legacy_scheduler is not None:
            return cast(SchedulerRuntime, legacy_scheduler)

    registry = get_scheduler_registry(request)

    try:
        return registry.get_runtime(scheduler_key)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scheduler: {scheduler_key}",
        ) from exc


def get_scheduler_configuration(
    request: Request,
    scheduler_key: str,
) -> SchedulerConfiguration:
    if scheduler_key == AIRPORT_SCHEDULER.key:
        legacy_scheduler = getattr(
            request.app.state,
            "airport_scheduler",
            None,
        )

        if legacy_scheduler is not None:
            return SchedulerConfiguration(
                identity=AIRPORT_SCHEDULER,
                enabled=settings.airport_scheduler_enabled,
                interval_seconds=settings.airport_scheduler_interval_seconds,
                run_on_startup=settings.airport_scheduler_run_on_startup,
                max_attempts=settings.airport_scheduler_max_attempts,
                retry_backoff_seconds=(
                    settings.airport_scheduler_retry_backoff_seconds
                ),
            )

    registry = get_scheduler_registry(request)

    try:
        registration = registry.get(scheduler_key)
    except KeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Unknown scheduler: {scheduler_key}",
        ) from exc

    if registration.identity.key == AIRPORT_SCHEDULER.key:
        return SchedulerConfiguration(
            identity=registration.identity,
            enabled=settings.airport_scheduler_enabled,
            interval_seconds=settings.airport_scheduler_interval_seconds,
            run_on_startup=settings.airport_scheduler_run_on_startup,
            max_attempts=settings.airport_scheduler_max_attempts,
            retry_backoff_seconds=(settings.airport_scheduler_retry_backoff_seconds),
        )

    if registration.identity.key == RAILWAY_SCHEDULER.key:
        return SchedulerConfiguration(
            identity=registration.identity,
            enabled=settings.railway_scheduler_enabled,
            interval_seconds=settings.railway_scheduler_interval_seconds,
            run_on_startup=settings.railway_scheduler_run_on_startup,
            max_attempts=settings.railway_scheduler_max_attempts,
            retry_backoff_seconds=(settings.railway_scheduler_retry_backoff_seconds),
        )

    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=(f"Scheduler configuration is missing: {registration.identity.key}"),
    )


def get_airport_scheduler(
    request: Request,
) -> AirportScheduler | None:
    legacy_scheduler = getattr(
        request.app.state,
        "airport_scheduler",
        None,
    )

    if legacy_scheduler is not None:
        return cast(AirportScheduler, legacy_scheduler)

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

    return cast(AirportScheduler | None, runtime)
