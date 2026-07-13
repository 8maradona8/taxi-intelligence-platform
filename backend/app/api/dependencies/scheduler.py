from fastapi import Request

from app.schedulers import AirportScheduler


def get_airport_scheduler(
    request: Request,
) -> AirportScheduler | None:
    return getattr(
        request.app.state,
        "airport_scheduler",
        None,
    )
