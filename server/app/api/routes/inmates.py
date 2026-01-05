"""
Inmates CRUD endpoints for Prison Roll Call API.
"""
from fastapi import APIRouter, HTTPException, Depends

from app.db.database import get_db
from app.db.repositories.inmate_repo import InmateRepository
from app.models.inmate import Inmate, InmateCreate, InmateUpdate

router = APIRouter()


def get_inmate_repo(db=Depends(get_db)) -> InmateRepository:
    """Dependency to get InmateRepository instance."""
    return InmateRepository(db)


@router.get("/inmates", response_model=list[Inmate])
async def list_inmates(repo: InmateRepository = Depends(get_inmate_repo)):
    """
    Get all inmates.
    
    Returns:
        list[Inmate]: List of all inmates
    """
    return repo.get_all()


@router.get("/inmates/{inmate_id}", response_model=Inmate)
async def get_inmate(
    inmate_id: str,
    repo: InmateRepository = Depends(get_inmate_repo)
):
    """
    Get a specific inmate by ID.
    
    Args:
        inmate_id: Inmate UUID
        
    Returns:
        Inmate: The requested inmate
        
    Raises:
        HTTPException: 404 if inmate not found
    """
    inmate = repo.get_by_id(inmate_id)
    if not inmate:
        raise HTTPException(status_code=404, detail=f"Inmate {inmate_id} not found")
    return inmate


@router.post("/inmates", response_model=Inmate, status_code=201)
async def create_inmate(
    inmate_data: InmateCreate,
    repo: InmateRepository = Depends(get_inmate_repo)
):
    """
    Create a new inmate.
    
    Args:
        inmate_data: Inmate creation data
        
    Returns:
        Inmate: The created inmate with generated ID
    """
    return repo.create(inmate_data)


@router.put("/inmates/{inmate_id}", response_model=Inmate)
async def update_inmate(
    inmate_id: str,
    inmate_data: InmateUpdate,
    repo: InmateRepository = Depends(get_inmate_repo)
):
    """
    Update an existing inmate.
    
    Args:
        inmate_id: Inmate UUID
        inmate_data: Inmate update data (partial update supported)
        
    Returns:
        Inmate: The updated inmate
        
    Raises:
        HTTPException: 404 if inmate not found
    """
    updated_inmate = repo.update(inmate_id, inmate_data)
    if not updated_inmate:
        raise HTTPException(status_code=404, detail=f"Inmate {inmate_id} not found")
    return updated_inmate


@router.delete("/inmates/{inmate_id}", status_code=204)
async def delete_inmate(
    inmate_id: str,
    repo: InmateRepository = Depends(get_inmate_repo)
):
    """
    Delete an inmate.
    
    Args:
        inmate_id: Inmate UUID
        
    Raises:
        HTTPException: 404 if inmate not found
    """
    success = repo.delete(inmate_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Inmate {inmate_id} not found")
