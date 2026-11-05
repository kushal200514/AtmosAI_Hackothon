from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timezone
import sys
import os

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.api.endpoints import router as api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="AtmosAI - AI-Powered Air Quality Forecasting & Environmental Intelligence Platform"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount API routers
app.include_router(api_router)

@app.get("/health", tags=["System"])
def health_check():
    """Health check endpoint providing system status, version, and server timestamp."""
    return {
        "status": "healthy",
        "service": "AtmosAI Environmental API",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "ai_provider": settings.AI_PROVIDER,
        "ml_engine": "LightGBM + Time-series persistence benchmark"
    }

@app.get("/", tags=["System"])
def root():
    return {
        "message": "Welcome to AtmosAI API - Breathe Smarter, Live Safer.",
        "docs_url": "/docs",
        "health": "/health",
        "api_routes": ["/api/locations", "/api/forecast/live", "/api/map/data"]
    }
