"""
Locations CRUD endpoints for Prison Roll Call API.
"""
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.db.database import get_db
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.connection_repo import ConnectionRepository
from app.models.location import Location, LocationCreate, LocationUpdate, LocationConnection
from app.services.pathfinding_service import PathfindingService, OptimizedRoute, RouteStop, WalkingDirections

router = APIRouter()


def get_location_repo(db=Depends(get_db)) -> LocationRepository:
    """Dependency to get LocationRepository instance."""
    return LocationRepository(db)


def get_connection_repo(db=Depends(get_db)) -> ConnectionRepository:
    """Dependency to get ConnectionRepository instance."""
    return ConnectionRepository(db)


def get_pathfinding_service(
    conn_repo: ConnectionRepository = Depends(get_connection_repo),
    loc_repo: LocationRepository = Depends(get_location_repo)
) -> PathfindingService:
    """Dependency to get PathfindingService instance."""
    return PathfindingService(conn_repo, loc_repo)


# Pydantic models for API responses
class WalkingDirectionsResponse(BaseModel):
    """Walking directions response model."""
    distance_meters: int
    time_seconds: int
    description: str
    connection_type: str


class RouteStopResponse(BaseModel):
    """Route stop response model."""
    location_id: str
    location_name: str
    building: str
    floor: int
    order: int
    walking_from_previous: WalkingDirectionsResponse | None


class RouteResponse(BaseModel):
    """Optimized route response model."""
    stops: list[RouteStopResponse]
    total_distance_meters: int
    total_time_seconds: int


class RouteRequest(BaseModel):
    """Request body for route calculation."""
    location_ids: list[str]


@router.get("/locations", response_model=list[Location])
async def list_locations(
    type: Optional[str] = None,
    repo: LocationRepository = Depends(get_location_repo)
):
    """
    Get all locations, optionally filtered by type.

    Args:
        type: Optional location type to filter by (prison, houseblock, wing, etc.)

    Returns:
        list[Location]: List of locations
    """
    if type:
        from app.models.location import LocationType
        try:
            location_type = LocationType(type)
            return repo.get_by_type(location_type)
        except ValueError:
            return []
    return repo.get_all()


@router.post("/locations/route", response_model=RouteResponse)
async def calculate_route(
    request: RouteRequest,
    service: PathfindingService = Depends(get_pathfinding_service)
):
    """
    Calculate an optimized route through specified locations.
    
    Orders locations logically by building then floor, and provides
    walking directions between consecutive stops.
    
    Args:
        request: RouteRequest containing list of location IDs to visit
        
    Returns:
        RouteResponse with ordered stops and total time/distance
    """
    route = service.calculate_route(request.location_ids)
    
    # Convert dataclass to response model
    stops = []
    for stop in route.stops:
        walking = None
        if stop.walking_from_previous:
            walking = WalkingDirectionsResponse(
                distance_meters=stop.walking_from_previous.distance_meters,
                time_seconds=stop.walking_from_previous.time_seconds,
                description=stop.walking_from_previous.description,
                connection_type=stop.walking_from_previous.connection_type
            )
        stops.append(RouteStopResponse(
            location_id=stop.location_id,
            location_name=stop.location_name,
            building=stop.building,
            floor=stop.floor,
            order=stop.order,
            walking_from_previous=walking
        ))
    
    return RouteResponse(
        stops=stops,
        total_distance_meters=route.total_distance_meters,
        total_time_seconds=route.total_time_seconds
    )


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


@router.get("/locations/{location_id}/connections", response_model=list[LocationConnection])
async def get_location_connections(
    location_id: str,
    repo: LocationRepository = Depends(get_location_repo),
    conn_repo: ConnectionRepository = Depends(get_connection_repo)
):
    """
    Get all connections from a specific location.
    
    Args:
        location_id: Location UUID
        
    Returns:
        list[LocationConnection]: All connections from this location
        
    Raises:
        HTTPException: 404 if location not found
    """
    # Verify location exists
    location = repo.get_by_id(location_id)
    if not location:
        raise HTTPException(status_code=404, detail=f"Location {location_id} not found")
    
    return conn_repo.get_from_location(location_id)
