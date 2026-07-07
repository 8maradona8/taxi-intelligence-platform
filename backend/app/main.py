from fastapi import FastAPI
from app.core.settings import settings


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
async def health() -> dict[str, str]:
    return {
        "status": "healthy",
    }