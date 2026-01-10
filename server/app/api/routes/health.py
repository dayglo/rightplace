"""
Health check endpoint for Prison Roll Call API.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.main import get_uptime_seconds

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)):
    """
    Health check endpoint.
    
    Returns server status, model status, enrollment count, and uptime.
    
    Returns:
        dict: Health check response with status information
    """
    # Count inmates with is_enrolled=True
    from app.db.repositories.inmate_repo import InmateRepository
    inmate_repo = InmateRepository(db)
    enrolled_count = db.execute(
        "SELECT COUNT(*) FROM inmates WHERE is_enrolled = 1"
    ).fetchone()[0]
    
    # Check if face recognition model is loaded
    # For now, we consider it loaded if we have any enrolled inmates
    model_loaded = enrolled_count > 0
    
    return {
        "status": "healthy",
        "model_loaded": model_loaded,
        "enrolled_count": enrolled_count,
        "uptime_seconds": get_uptime_seconds(),
    }
