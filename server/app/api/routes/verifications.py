"""
Verification records API endpoints.

Provides REST API for accessing verification history and records.
"""
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, status

from app.db.database import get_db
from app.db.repositories.verification_repo import VerificationRepository
from app.models.verification import Verification


router = APIRouter()


def get_verification_repo(db=Depends(get_db)) -> VerificationRepository:
    """
    Dependency injection for VerificationRepository.

    Args:
        db: Database connection from dependency

    Returns:
        VerificationRepository instance
    """
    return VerificationRepository(db)


@router.get("/verifications/inmate/{inmate_id}", response_model=list[Verification])
async def get_inmate_verifications(
    inmate_id: str,
    limit: Optional[int] = None,
    repo: VerificationRepository = Depends(get_verification_repo),
):
    """
    Get verification history for an inmate.

    Args:
        inmate_id: Inmate ID
        limit: Optional limit on number of results
        repo: Verification repository dependency

    Returns:
        List of verifications for the inmate, sorted by timestamp descending
    """
    all_verifications = repo.get_by_inmate(inmate_id)

    if limit and limit > 0:
        return all_verifications[:limit]

    return all_verifications


@router.get("/verifications/roll-call/{roll_call_id}", response_model=list[Verification])
async def get_roll_call_verifications(
    roll_call_id: str,
    repo: VerificationRepository = Depends(get_verification_repo),
):
    """
    Get all verifications for a roll call.

    Args:
        roll_call_id: Roll call ID
        repo: Verification repository dependency

    Returns:
        List of verifications for the roll call
    """
    return repo.get_by_roll_call(roll_call_id)


@router.get("/verifications/location/{location_id}", response_model=list[Verification])
async def get_location_verifications(
    location_id: str,
    repo: VerificationRepository = Depends(get_verification_repo),
):
    """
    Get all verifications for a location.

    Args:
        location_id: Location ID
        repo: Verification repository dependency

    Returns:
        List of verifications for the location
    """
    return repo.get_by_location(location_id)


@router.get("/verifications/{verification_id}", response_model=Verification)
async def get_verification(
    verification_id: str,
    repo: VerificationRepository = Depends(get_verification_repo),
):
    """
    Get verification by ID.

    Args:
        verification_id: Verification ID
        repo: Verification repository dependency

    Returns:
        Verification record

    Raises:
        HTTPException: 404 if not found
    """
    verification = repo.get_by_id(verification_id)
    if not verification:
        raise HTTPException(
            status_code=404,
            detail=f"Verification {verification_id} not found",
        )
    return verification
