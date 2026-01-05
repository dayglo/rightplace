"""
Data models package.

Exports all Pydantic models for use throughout the application.
"""
from app.models.face import (
    BoundingBox,
    DetectionResult,
    FaceLandmarks,
    MatchRecommendation,
    MatchResult,
    QualityIssue,
)
from app.models.inmate import Inmate, InmateCreate, InmateUpdate
from app.models.location import Location, LocationType
from app.models.rollcall import RollCall, RollCallStatus, RouteStop
from app.models.verification import (
    ManualOverrideReason,
    Verification,
    VerificationStatus,
)

__all__ = [
    # Inmate models
    "Inmate",
    "InmateCreate",
    "InmateUpdate",
    # Location models
    "Location",
    "LocationType",
    # Roll call models
    "RollCall",
    "RollCallStatus",
    "RouteStop",
    # Verification models
    "Verification",
    "VerificationStatus",
    "ManualOverrideReason",
    # Face recognition models
    "BoundingBox",
    "FaceLandmarks",
    "QualityIssue",
    "DetectionResult",
    "MatchRecommendation",
    "MatchResult",
]
