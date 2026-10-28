
from fastapi import FastAPI

from app.core.config import settings
from app.core.logging_config import configure_logging

configure_logging()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Satellite-based vegetation change monitoring "
        "for Telangana, India."
    ),
)


@app.get("/", tags=["General"])
def root() -> dict[str, str]:
    return {
        "message": "Welcome to ForestWatch AI",
        "status": "running",
        "version": settings.app_version,
    }


@app.get("/health", tags=["Health"])
def health_check() -> dict[str, str]:
    return {
        "status": "healthy",
        "service": "forestwatch-api",
    }
