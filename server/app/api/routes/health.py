"""
Health check endpoint for Prison Roll Call API.
"""
from fastapi import APIRouter

from app.main import get_uptime_seconds

router = APIRouter()


@router.get("/health")
async def health_check():
    """
    Health check endpoint.
    
    Returns server status, model status, enrollment count, and uptime.
    
    Returns:
        dict: Health check response with status information
    """
    # For MVP, model_loaded is always False (ML pipeline not implemented yet)
    # enrolled_count will be 0 until we implement enrollment
    return {
        "status": "healthy",
        "model_loaded": False,
        "enrolled_count": 0,
        "uptime_seconds": get_uptime_seconds(),
    }
