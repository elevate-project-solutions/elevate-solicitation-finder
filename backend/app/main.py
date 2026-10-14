from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name + " API",
    description="Backend API for government solicitation discovery and analysis.",
    version="0.1.0",
)

#Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
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
