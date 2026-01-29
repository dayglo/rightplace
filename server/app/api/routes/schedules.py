"""
Schedule API endpoints.

Provides REST API for schedule management with conflict detection.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status

from app.db.database import get_db
from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.services.schedule_service import ScheduleService
from app.models.schedule import (
    ScheduleEntry,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
)


router = APIRouter()


def get_schedule_service(db=Depends(get_db)) -> ScheduleService:
    """
    Dependency injection for ScheduleService.

    Args:
        db: Database connection from dependency

    Returns:
        ScheduleService instance
    """
    schedule_repo = ScheduleRepository(db)
    inmate_repo = InmateRepository(db)
    location_repo = LocationRepository(db)
    return ScheduleService(schedule_repo, inmate_repo, location_repo)


@router.post("/schedules", response_model=ScheduleEntry, status_code=status.HTTP_201_CREATED)
async def create_schedule_entry(
    entry: ScheduleEntryCreate,
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Create a new schedule entry.

    Args:
        entry: Schedule entry data
        service: Schedule service dependency

    Returns:
        Created schedule entry

    Raises:
        HTTPException: 400 if inmate/location not found, 409 if conflict
    """
    try:
        return service.create_schedule_entry(entry)
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=400, detail=str(e))
        elif "conflict" in error_msg:
            raise HTTPException(status_code=409, detail=str(e))
        raise


@router.get("/schedules/{entry_id}", response_model=ScheduleEntry)
async def get_schedule_entry(
    entry_id: str,
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Get schedule entry by ID.

    Args:
        entry_id: Schedule entry ID
        service: Schedule service dependency

    Returns:
        Schedule entry

    Raises:
        HTTPException: 404 if not found
    """
    entry = service.schedule_repo.get_by_id(entry_id)
    if not entry:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule entry {entry_id} not found",
        )
    return entry


@router.put("/schedules/{entry_id}", response_model=ScheduleEntry)
async def update_schedule_entry(
    entry_id: str,
    update: ScheduleEntryUpdate,
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Update schedule entry.

    Args:
        entry_id: Schedule entry ID
        update: Fields to update
        service: Schedule service dependency

    Returns:
        Updated schedule entry

    Raises:
        HTTPException: 404 if not found, 409 if conflict
    """
    try:
        return service.update_schedule_entry(entry_id, update)
    except ValueError as e:
        error_msg = str(e).lower()
        if "not found" in error_msg:
            raise HTTPException(status_code=404, detail=str(e))
        elif "conflict" in error_msg:
            raise HTTPException(status_code=409, detail=str(e))
        raise


@router.delete("/schedules/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule_entry(
    entry_id: str,
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Delete schedule entry.

    Args:
        entry_id: Schedule entry ID
        service: Schedule service dependency

    Raises:
        HTTPException: 404 if not found
    """
    success = service.delete_schedule_entry(entry_id)
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Schedule entry {entry_id} not found",
        )


@router.get("/schedules/inmate/{inmate_id}", response_model=list[ScheduleEntry])
async def get_inmate_schedules(
    inmate_id: str,
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Get all schedule entries for an inmate.

    Args:
        inmate_id: Inmate ID
        service: Schedule service dependency

    Returns:
        List of schedule entries sorted by day/time
    """
    return service.get_inmate_schedule(inmate_id)


@router.get("/schedules/location/{location_id}", response_model=list[ScheduleEntry])
async def get_location_schedules(
    location_id: str,
    day_of_week: Optional[int] = None,
    service: ScheduleService = Depends(get_schedule_service),
):
    """
    Get all schedule entries for a location.

    Args:
        location_id: Location ID
        day_of_week: Optional day filter (0-6)
        service: Schedule service dependency

    Returns:
        List of schedule entries for the location
    """
    return service.get_location_schedule(location_id, day_of_week)
