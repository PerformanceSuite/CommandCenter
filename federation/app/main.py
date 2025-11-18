# federation/app/main.py
from fastapi import FastAPI
from app.config import settings
import logging

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Federation Service",
    version="0.9.0",
    description="Multi-project catalog and orchestration"
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "federation",
        "version": "0.9.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)
