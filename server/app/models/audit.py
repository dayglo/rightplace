"""
Audit log data models.

Defines models for audit trail entries and action tracking.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel


class AuditAction(str, Enum):
    """Auditable action types."""

    INMATE_CREATED = "inmate_created"
    INMATE_UPDATED = "inmate_updated"
    INMATE_DELETED = "inmate_deleted"
    FACE_ENROLLED = "face_enrolled"
    FACE_UNENROLLED = "face_unenrolled"
    ROLLCALL_STARTED = "rollcall_started"
    ROLLCALL_COMPLETED = "rollcall_completed"
    ROLLCALL_CANCELLED = "rollcall_cancelled"
    VERIFICATION_RECORDED = "verification_recorded"
    MANUAL_OVERRIDE_USED = "manual_override_used"
    STOP_SKIPPED = "stop_skipped"
    POLICY_UPDATED = "policy_updated"
    QUEUE_SYNCED = "queue_synced"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"


class AuditEntry(BaseModel):
    """Audit trail entry."""

    id: str
    timestamp: datetime
    user_id: str  # officer_id in database
    action: str  # AuditAction value
    entity_type: str
    entity_id: str
    details: Optional[dict] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
