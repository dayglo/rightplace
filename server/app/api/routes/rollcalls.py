"""
Roll Call CRUD endpoints for Prison Roll Call API.
"""
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel

from app.db.database import get_db
from app.db.repositories.rollcall_repo import RollCallRepository
from app.db.repositories.verification_repo import VerificationRepository
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.connection_repo import ConnectionRepository
from app.dependencies import get_audit_service
from app.services.rollcall_service import RollCallService
from app.services.pathfinding_service import PathfindingService
from app.services.rollcall_generator_service import RollCallGeneratorService
from app.services.audit_service import AuditService
from app.models.audit import AuditAction
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
class RollCallSummary(BaseModel):
    """Roll call with verification statistics for list view."""
    id: str
    name: str
    status: str
    scheduled_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    officer_id: str
    notes: str = ""
    # Statistics
    total_stops: int
    expected_inmates: int
    verified_inmates: int
    progress_percentage: float


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
@router.get("/rollcalls", response_model=list[RollCallSummary])
async def list_rollcalls(
    service: RollCallService = Depends(get_rollcall_service),
):
    """
    Get all roll calls with verification statistics.

    Returns:
        list[RollCallSummary]: List of all roll calls with progress stats
    """
    repo = service.rollcall_repo
    all_rollcalls = repo.get_all()

    # Enrich each roll call with statistics
    summaries = []
    for rollcall in all_rollcalls:
        stats = service.get_progress_stats(rollcall.id)
        summary = RollCallSummary(
            id=rollcall.id,
            name=rollcall.name,
            status=rollcall.status.value,
            scheduled_at=rollcall.scheduled_at,
            started_at=rollcall.started_at,
            completed_at=rollcall.completed_at,
            officer_id=rollcall.officer_id,
            notes=rollcall.notes,
            total_stops=stats["total_stops"],
            expected_inmates=stats["expected_inmates"],
            verified_inmates=stats["verified_inmates"],
            progress_percentage=stats["progress_percentage"],
        )
        summaries.append(summary)

    return summaries


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
    request: Request,
    service: RollCallService = Depends(get_rollcall_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Start a scheduled roll call.

    Args:
        rollcall_id: Roll call UUID
        request: FastAPI request for user context
        service: Roll call service
        audit_service: Audit service for logging

    Returns:
        RollCall: The updated roll call

    Raises:
        HTTPException: 404 if roll call not found, 400 if already started
    """
    try:
        rollcall = service.start_roll_call(rollcall_id)

        # Log the action
        audit_service.log_action(
            user_id=request.state.user_id,
            action=AuditAction.ROLLCALL_STARTED,
            entity_type="rollcall",
            entity_id=rollcall_id,
            details={
                "location": rollcall.route[0].location_id if rollcall.route else None,
                "expected_stops": len(rollcall.route),
            },
            ip_address=request.state.client_ip,
            user_agent=request.state.user_agent,
        )

        return rollcall
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollcalls/{rollcall_id}/complete", response_model=RollCall)
async def complete_rollcall(
    rollcall_id: str,
    request: Request,
    service: RollCallService = Depends(get_rollcall_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Complete an in-progress roll call.

    Args:
        rollcall_id: Roll call UUID
        request: FastAPI request for user context
        service: Roll call service
        audit_service: Audit service for logging

    Returns:
        RollCall: The updated roll call

    Raises:
        HTTPException: 404 if roll call not found, 400 if not in progress
    """
    try:
        # Get stats before completing
        stats = service.get_progress_stats(rollcall_id)

        rollcall = service.complete_roll_call(rollcall_id)

        # Log the action
        audit_service.log_action(
            user_id=request.state.user_id,
            action=AuditAction.ROLLCALL_COMPLETED,
            entity_type="rollcall",
            entity_id=rollcall_id,
            details={
                "total_stops": stats["total_stops"],
                "verified_inmates": stats["verified_inmates"],
                "expected_inmates": stats["expected_inmates"],
                "progress_percentage": stats["progress_percentage"],
            },
            ip_address=request.state.client_ip,
            user_agent=request.state.user_agent,
        )

        return rollcall
    except ValueError as e:
        if "not found" in str(e):
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/rollcalls/{rollcall_id}/cancel", response_model=RollCall)
async def cancel_rollcall(
    rollcall_id: str,
    cancel_request: CancelRequest,
    request: Request,
    service: RollCallService = Depends(get_rollcall_service),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Cancel a roll call with reason.

    Args:
        rollcall_id: Roll call UUID
        cancel_request: Cancellation request with reason
        request: FastAPI request for user context
        service: Roll call service
        audit_service: Audit service for logging

    Returns:
        RollCall: The updated roll call

    Raises:
        HTTPException: 404 if roll call not found, 400 if reason missing
    """
    try:
        rollcall = service.cancel_roll_call(rollcall_id, cancel_request.reason)

        # Log the action
        audit_service.log_action(
            user_id=request.state.user_id,
            action=AuditAction.ROLLCALL_CANCELLED,
            entity_type="rollcall",
            entity_id=rollcall_id,
            details={"reason": cancel_request.reason},
            ip_address=request.state.client_ip,
            user_agent=request.state.user_agent,
        )

        return rollcall
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
    request: Request,
    verification_repo: VerificationRepository = Depends(get_verification_repo),
    audit_service: AuditService = Depends(get_audit_service),
):
    """
    Record a verification for a roll call.

    Args:
        rollcall_id: Roll call UUID
        verification_data: Verification data
        request: FastAPI request for user context
        verification_repo: Verification repository
        audit_service: Audit service for logging

    Returns:
        Verification: The created verification record

    Raises:
        HTTPException: 404 if roll call not found
    """
    try:
        # Create verification
        verification = verification_repo.create(
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

        # Log the action
        action = (
            AuditAction.MANUAL_OVERRIDE_USED
            if verification_data.is_manual_override
            else AuditAction.VERIFICATION_RECORDED
        )

        audit_service.log_action(
            user_id=request.state.user_id,
            action=action,
            entity_type="verification",
            entity_id=verification.id,
            details={
                "inmate_id": verification_data.inmate_id,
                "location_id": verification_data.location_id,
                "confidence": verification_data.confidence,
                "status": verification_data.status.value,
                "manual_override_reason": (
                    verification_data.manual_override_reason.value
                    if verification_data.manual_override_reason
                    else None
                ),
            },
            ip_address=request.state.client_ip,
            user_agent=request.state.user_agent,
        )

        return verification
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


# Generate Roll Call Endpoint
class GenerateRollCallRequest(BaseModel):
    """Request body for generating a roll call from location and schedule."""
    location_ids: list[str]
    scheduled_at: datetime
    include_empty: bool = True
    name: str | None = None
    officer_id: str = "officer-001"


class RouteStopResponse(BaseModel):
    """A stop in the roll call route."""
    order: int
    location_id: str
    location_name: str
    location_type: str
    building: str
    floor: int
    is_occupied: bool
    expected_count: int
    walking_distance_meters: int
    walking_time_seconds: int


class GeneratedRollCallResponse(BaseModel):
    """Response for generated roll call."""
    location_ids: list[str]
    location_names: list[str]
    scheduled_at: datetime
    route: list[RouteStopResponse]
    summary: dict


def get_generator_service(db=Depends(get_db)) -> RollCallGeneratorService:
    """Dependency to get RollCallGeneratorService instance."""
    location_repo = LocationRepository(db)
    inmate_repo = InmateRepository(db)
    schedule_repo = ScheduleRepository(db)
    connection_repo = ConnectionRepository(db)
    # PathfindingService expects (connection_repo, location_repo) order
    pathfinding_service = PathfindingService(connection_repo, location_repo)
    
    return RollCallGeneratorService(
        location_repo=location_repo,
        inmate_repo=inmate_repo,
        schedule_repo=schedule_repo,
        pathfinding_service=pathfinding_service,
    )


@router.post("/rollcalls/generate", response_model=GeneratedRollCallResponse)
async def generate_rollcall(
    request: GenerateRollCallRequest,
    generator: RollCallGeneratorService = Depends(get_generator_service),
):
    """
    Generate a schedule-aware roll call for one or more locations.

    Takes one or more locations (cells, landings, wings, or houseblocks) and
    generates an optimal walking route through all cells, with expected prisoner
    counts based on the schedule at the specified time.

    Supports flexible selection:
    - Single location: ["houseblock-1"] - all cells in houseblock
    - Multiple wings: ["a-wing", "b-wing"]
    - Two landings: ["a1-landing", "a2-landing"]
    - Specific cells: ["cell-101", "cell-205", "cell-310"]
    - Mixed hierarchy: ["b-wing", "a1-landing", "cell-405"]

    Args:
        request: Generation parameters (location_ids, scheduled_at, etc.)

    Returns:
        GeneratedRollCallResponse: The generated roll call with route and summary

    Raises:
        HTTPException: 404 if location not found, 400 on other errors
    """
    try:
        result = generator.generate_roll_call(
            location_ids=request.location_ids,
            scheduled_at=request.scheduled_at,
            include_empty=request.include_empty,
        )

        # Convert to response model
        route_stops = [
            RouteStopResponse(
                order=stop.order,
                location_id=stop.location_id,
                location_name=stop.location_name,
                location_type=stop.location_type,
                building=stop.building,
                floor=stop.floor,
                is_occupied=stop.is_occupied,
                expected_count=stop.expected_count,
                walking_distance_meters=stop.walking_distance_meters,
                walking_time_seconds=stop.walking_time_seconds,
            )
            for stop in result.route
        ]

        return GeneratedRollCallResponse(
            location_ids=result.location_ids,
            location_names=result.location_names,
            scheduled_at=result.scheduled_at,
            route=route_stops,
            summary={
                "total_locations": result.total_locations,
                "occupied_locations": result.occupied_locations,
                "empty_locations": result.empty_locations,
                "total_prisoners_expected": result.total_prisoners_expected,
                "estimated_time_seconds": result.estimated_time_seconds,
            },
        )
    except ValueError as e:
        if "not found" in str(e).lower():
            raise HTTPException(status_code=404, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))


class ExpectedPrisonerResponse(BaseModel):
    """A prisoner expected at a location."""
    inmate_id: str
    inmate_number: str
    first_name: str
    last_name: str
    is_enrolled: bool
    home_cell_id: str | None
    is_at_home_cell: bool
    current_activity: str
    next_appointment: dict | None
    priority_score: int


class ExpectedPrisonersResponse(BaseModel):
    """Response for expected prisoners at a location."""
    location_id: str
    expected_prisoners: list[ExpectedPrisonerResponse]
    total_expected: int


@router.get("/rollcalls/expected/{location_id}")
async def get_expected_prisoners(
    location_id: str,
    at_time: datetime | None = None,
    generator: RollCallGeneratorService = Depends(get_generator_service),
):
    """
    Get prisoners expected at a location at a specific time.
    
    Returns prisoners sorted by priority (those with imminent appointments first).
    
    Args:
        location_id: The location to check
        at_time: Time to check (defaults to now)
        
    Returns:
        ExpectedPrisonersResponse: List of expected prisoners with priority info
    """
    check_time = at_time or datetime.now()
    
    expected = generator.get_expected_prisoners(location_id, check_time)
    
    prisoners = [
        ExpectedPrisonerResponse(
            inmate_id=p.inmate.id,
            inmate_number=p.inmate.inmate_number,
            first_name=p.inmate.first_name,
            last_name=p.inmate.last_name,
            is_enrolled=p.inmate.is_enrolled,
            home_cell_id=p.home_cell_id,
            is_at_home_cell=p.is_at_home_cell,
            current_activity=p.current_activity,
            next_appointment={
                "activity_type": p.next_appointment.activity_type,
                "location_name": p.next_appointment.location_name,
                "start_time": p.next_appointment.start_time,
                "minutes_until": p.next_appointment.minutes_until,
                "is_urgent": p.next_appointment.is_urgent,
            } if p.next_appointment else None,
            priority_score=p.priority_score,
        )
        for p in expected
    ]
    
    return ExpectedPrisonersResponse(
        location_id=location_id,
        expected_prisoners=prisoners,
        total_expected=len(prisoners),
    )
