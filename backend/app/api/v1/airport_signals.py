from dataclasses import asdict

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import (
    get_airport_signal_history_service,
)
from app.application.dto import AirportSignalHistoryResponse
from app.services.airport_signal_history_service import (
    AirportSignalHistoryService,
)


router = APIRouter(
    prefix="/airports",
    tags=["Airport Intelligence"],
)


@router.get("/{airport_code}/signals")
async def get_airport_signal_history(
    airport_code: str,
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
    ),
    service: AirportSignalHistoryService = Depends(get_airport_signal_history_service),
):
    normalized_code = airport_code.strip().upper()

    if normalized_code != "SOF":
        return {
            "airport": normalized_code,
            "count": 0,
            "signals": [],
        }

    signals = await service.get_history(
        limit=limit,
    )

    response = AirportSignalHistoryResponse.from_models(signals)

    return asdict(response)
