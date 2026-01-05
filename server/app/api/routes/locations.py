"""
Locations CRUD endpoints for Prison Roll Call API.
"""
from fastapi import APIRouter, HTTPException, Depends

from app.db.database import get_db
from app.db.repositories.location_repo import LocationRepository
from app.models.location import Location, LocationCreate, LocationUpdate

router = APIRouter()


def get_location_repo(db=Depends(get_db)) -> LocationRepository:
    """Dependency to get LocationRepository instance."""
    return LocationRepository(db)


@router.get("/locations", response_model=list[Location])
async def list_locations(repo: LocationRepository = Depends(get_location_repo)):
    """
    Get all locations.
    
    Returns:
        list[Location]: List of all locations
    """
    return repo.get_all()


@router.get("/locations/{location_id}", response_model=Location)
async def get_location(
    location_id: str,
    repo: LocationRepository = Depends(get_location_repo)
):
    """
    Get a specific location by ID.
    
    Args:
        location_id: Location UUID
        
    Returns:
        Location: The requested location
        
    Raises:
        HTTPException: 404 if location not found
    """
    location = repo.get_by_id(location_id)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return location


@router.post("/locations", response_model=Location, status_code=201)
async def create_location(
    location_data: LocationCreate,
    repo: LocationRepository = Depends(get_location_repo)
):
    """
    Create a new location.
    
    Args:
        location_data: Location creation data
        
    Returns:
        Location: The created location with generated ID
    """
    return repo.create(location_data)


@router.put("/locations/{location_id}", response_model=Location)
async def update_location(
    location_id: str,
    location_data: LocationUpdate,
    repo: LocationRepository = Depends(get_location_repo)
):
    """
    Update an existing location.
    
    Args:
        location_id: Location UUID
        location_data: Location update data (partial update supported)
        
    Returns:
        Location: The updated location
        
    Raises:
        HTTPException: 404 if location not found
    """
    updated_location = repo.update(location_id, location_data)
    if not updated_location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    return updated_location


@router.delete("/locations/{location_id}", status_code=204)
async def delete_location(
    location_id: str,
    repo: LocationRepository = Depends(get_location_repo)
):
    """
    Delete a location.
    
    Args:
        location_id: Location UUID
        
    Raises:
        HTTPException: 404 if location not found
    """
    success = repo.delete(location_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
