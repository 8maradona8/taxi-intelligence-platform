from fastapi import FastAPI


app = FastAPI(
    title="Taxi Intelligence Platform",
    version="0.1.0",
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