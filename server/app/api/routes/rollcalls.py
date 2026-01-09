"""
Roll Call CRUD endpoints for Prison Roll Call API.
"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.db.database import get_db
from app.db.repositories.rollcall_repo import RollCallRepository
from app.db.repositories.verification_repo import VerificationRepository
from app.services.rollcall_service import RollCallService
from app.models.rollcall import RollCall, RollCallCreate
from app.models.verification import (
    Verification,
    VerificationStatus,
    ManualOverrideReason,
)

router = APIRouter()


# Dependency injection helpers
def get_rollcall_repo(db=Depends(get_db)) -> RollCallRepository:
    """Dependency to get RollCallRepository instance."""
    return RollCallRepository(db)


def get_verification_repo(db=Depends(get_db)) -> VerificationRepository:
    """Dependency to get VerificationRepository instance."""
    return VerificationRepository(db)


def get_rollcall_service(
    rollcall_repo: RollCallRepository = Depends(get_rollcall_repo),
    verification_repo: VerificationRepository = Depends(get_verification_repo),
) -> RollCallService:
    """Dependency to get RollCallService instance."""
    return RollCallService(rollcall_repo, verification_repo)


# Request/Response models
class CancelRequest(BaseModel):
    """Request body for cancelling a roll call."""
    reason: str


class VerificationRequest(BaseModel):
    """Request body for recording a verification."""
    inmate_id: str
    location_id: str
    status: VerificationStatus
    confidence: float
    is_manual_override: bool = False
    manual_override_reason: ManualOverrideReason | None = None
    photo_uri: str | None = None
    notes: str = ""


# CRUD Endpoints
@router.get("/rollcalls", response_model=list[RollCall])
async def list_rollcalls(
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Get all roll calls.
    
    Returns:
        list[RollCall]: List of all roll calls
    """
    repo = service.rollcall_repo
    return repo.get_all()


@router.get("/rollcalls/{rollcall_id}", response_model=RollCall)
async def get_rollcall(
    rollcall_id: str,
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Get a specific roll call by ID.
    
    Args:
        rollcall_id: Roll call UUID
        
    Returns:
        RollCall: The requested roll call
        
    Raises:
        HTTPException: 404 if roll call not found
    """
    repo = service.rollcall_repo
    rollcall = repo.get_by_id(rollcall_id)
    if not rollcall:
        raise HTTPException(
            status_code=404, detail=f"Roll call {rollcall_id} not found"
        )
    return rollcall


@router.post("/rollcalls", response_model=RollCall, status_code=201)
async def create_rollcall(
    rollcall_data: RollCallCreate,
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Create a new roll call.
    
    Args:
        rollcall_data: Roll call creation data
        
    Returns:
        RollCall: The created roll call with generated ID
        
    Raises:
        HTTPException: 400 if validation fails
    """
    try:
        return service.create_roll_call(rollcall_data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/rollcalls/{rollcall_id}", status_code=204)
async def delete_rollcall(
    rollcall_id: str,
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Delete a roll call.
    
    Args:
        rollcall_id: Roll call UUID
        
    Raises:
        HTTPException: 404 if roll call not found
    """
    repo = service.rollcall_repo
    success = repo.delete(rollcall_id)
    if not success:
        raise HTTPException(
            status_code=404, detail=f"Roll call {rollcall_id} not found"
        )


# Status Transition Endpoints
@router.post("/rollcalls/{rollcall_id}/start", response_model=RollCall)
async def start_rollcall(
    rollcall_id: str,
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Start a scheduled roll call.
    
    Args:
        rollcall_id: Roll call UUID
        
    Returns:
        RollCall: The updated roll call
        
    Raises:
        HTTPException: 404 if roll call not found, 400 if already started
    """
    try:
        return service.start_roll_call(rollcall_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollcalls/{rollcall_id}/complete", response_model=RollCall)
async def complete_rollcall(
    rollcall_id: str,
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Complete an in-progress roll call.
    
    Args:
        rollcall_id: Roll call UUID
        
    Returns:
        RollCall: The updated roll call
        
    Raises:
        HTTPException: 404 if roll call not found, 400 if not in progress
    """
    try:
        return service.complete_roll_call(rollcall_id)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollcalls/{rollcall_id}/cancel", response_model=RollCall)
async def cancel_rollcall(
    rollcall_id: str,
    cancel_request: CancelRequest,
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Cancel a roll call with reason.
    
    Args:
        rollcall_id: Roll call UUID
        cancel_request: Cancellation request with reason
        
    Returns:
        RollCall: The updated roll call
        
    Raises:
        HTTPException: 404 if roll call not found, 400 if reason missing
    """
    try:
        return service.cancel_roll_call(rollcall_id, cancel_request.reason)
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


# Verification Recording
@router.post(
    "/rollcalls/{rollcall_id}/verification",
    response_model=Verification,
    status_code=201,
)
async def record_verification(
    rollcall_id: str,
    verification_data: VerificationRequest,
    verification_repo: VerificationRepository = Depends(get_verification_repo),
):
    """
    Record a verification for a roll call.
    
    Args:
        rollcall_id: Roll call UUID
        verification_data: Verification data
        
    Returns:
        Verification: The created verification record
        
    Raises:
        HTTPException: 404 if roll call not found
    """
    try:
        return verification_repo.create(
            roll_call_id=rollcall_id,
            inmate_id=verification_data.inmate_id,
            location_id=verification_data.location_id,
            status=verification_data.status,
            confidence=verification_data.confidence,
            photo_uri=verification_data.photo_uri,
            is_manual_override=verification_data.is_manual_override,
            manual_override_reason=verification_data.manual_override_reason,
            notes=verification_data.notes,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))