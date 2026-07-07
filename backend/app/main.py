from fastapi import FastAPI
from app.core.logging import logger, setup_logging
from app.core.settings import settings


setup_logging()


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    )

@app.get("/")
async def root() -> dict[str, str]:
    return {
        "status": "online",
        "service": "TIP Backend",
    }

@app.get("/health")
def health_check():
    logger.info("health_check_called")

    return {
        "status": "healthy",
        "environment": settings.environment,
    }

@app.get("/health")
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }