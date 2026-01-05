"""
Roll call data models.

Defines models for roll calls, route stops, and workflow state.
"""
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel


class RollCallStatus(str, Enum):
    """Roll call workflow states."""

    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class RouteStop(BaseModel):
    """A stop in a roll call route."""

    id: str
    location_id: str
    order: int
    expected_inmates: list[str]
    status: Literal["pending", "current", "completed", "skipped"] = "pending"
    arrived_at: datetime | None = None
    completed_at: datetime | None = None
    skip_reason: str | None = None


class RollCall(BaseModel):
    """Complete roll call with route and metadata."""

    id: str
    name: str
    status: RollCallStatus
    scheduled_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_reason: str | None = None
    route: list[RouteStop]
    officer_id: str
    notes: str = ""
