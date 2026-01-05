"""
Verification data models.

Defines models for inmate verification records and manual override tracking.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class VerificationStatus(str, Enum):
    """Verification result states."""

    VERIFIED = "verified"
    NOT_FOUND = "not_found"
    WRONG_LOCATION = "wrong_location"
    MANUAL = "manual"
    PENDING = "pending"


class ManualOverrideReason(str, Enum):
    """Reasons for manual verification override."""

    FACIAL_INJURY = "facial_injury"
    LIGHTING_CONDITIONS = "lighting_conditions"
    TECHNICAL_FAILURE = "technical_failure"
    NOT_ENROLLED = "not_enrolled"
    NETWORK_UNAVAILABLE = "network_unavailable"
    OTHER = "other"


class Verification(BaseModel):
    """Inmate verification record."""

    id: str
    roll_call_id: str
    inmate_id: str
    location_id: str
    status: VerificationStatus
    confidence: float
    photo_uri: str | None = None
    timestamp: datetime
    is_manual_override: bool = False
    manual_override_reason: ManualOverrideReason | None = None
    notes: str = ""
