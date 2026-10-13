from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name + " API",
    description="Backend API for government solicitation discovery and analysis.",
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "message": "Elevate Solicitation Finder API",
        "status": "running",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "environment": settings.app_env,
    }
