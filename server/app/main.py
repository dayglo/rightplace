"""
FastAPI application entry point for Prison Roll Call server.
"""
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import Settings

# Track server startup time for uptime calculation
_startup_time = time.time()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    
    Handles startup and shutdown events.
    """
    # Startup
    global _startup_time
    _startup_time = time.time()
    yield
    # Shutdown
    pass


def create_app(settings: Settings | None = None) -> FastAPI:
    """
    Create and configure the FastAPI application.
    
    Args:
        settings: Optional settings override (useful for testing)
    
    Returns:
        Configured FastAPI application
    """
    if settings is None:
        settings = Settings()
    
    app = FastAPI(
        title="Prison Roll Call API",
        version="1.0.0",
        description="ML-powered inmate verification system",
        lifespan=lifespan,
    )
    
    # CORS middleware for mobile app
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict to mobile app origin
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Register routes
    from app.api.routes import enrollment, health, inmates, locations, rollcalls, verification
    app.include_router(health.router, prefix="/api/v1", tags=["health"])
    app.include_router(inmates.router, prefix="/api/v1", tags=["inmates"])
    app.include_router(locations.router, prefix="/api/v1", tags=["locations"])
    app.include_router(enrollment.router, prefix="/api/v1", tags=["enrollment"])
    app.include_router(verification.router, prefix="/api/v1", tags=["verification"])
    app.include_router(rollcalls.router, prefix="/api/v1", tags=["rollcalls"])
    
    return app


def get_uptime_seconds() -> float:
    """Get server uptime in seconds."""
    return time.time() - _startup_time


# Create default app instance
app = create_app()
