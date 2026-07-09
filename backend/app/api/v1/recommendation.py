from dataclasses import asdict

from fastapi import APIRouter, Depends

from app.api.dependencies import get_snapshot_handler
from app.application.dto import CitySnapshotResponse
from app.application.handlers import GetCitySnapshotHandler
from app.application.queries import GetCitySnapshotQuery


router = APIRouter(
    prefix="/cities",
    tags=["City Intelligence"],
)


@router.get("/{city_name}/recommendation")
async def get_city_recommendation(
    city_name: str,
    handler: GetCitySnapshotHandler = Depends(get_snapshot_handler),
):
    snapshot = handler.handle(
        GetCitySnapshotQuery(
            city_name=city_name,
        )
    )

    response = CitySnapshotResponse.from_domain(snapshot)

    if response.best_recommendation is None:
        return {
            "recommendation": None,
            "message": "No recommendation available",
        }

    return asdict(response.best_recommendation)