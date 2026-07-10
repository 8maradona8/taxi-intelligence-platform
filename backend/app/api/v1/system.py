from fastapi import APIRouter

from app.core.settings import settings
from app.database.health import check_database


router = APIRouter(
    prefix="/system",
    tags=["System"],
)


@router.get("/health")
async def system_health():
    database_ok = await check_database()

    return {
        "status": "healthy" if database_ok else "unhealthy",
        "service": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "database": {
            "status": "connected" if database_ok else "disconnected",
        },
    }
