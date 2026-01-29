"""
Schedule data models.

Defines models for prisoner schedules/regimes and activity types.
"""
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator


class ActivityType(str, Enum):
    """Types of scheduled activities in a prison regime."""

    ROLL_CHECK = "roll_check"      # Mandatory headcount
    LOCK_UP = "lock_up"            # In cell, locked
    UNLOCK = "unlock"              # Cell unlocked
    MEAL = "meal"                  # Breakfast/lunch/dinner
    WORK = "work"                  # Workshop assignment
    EDUCATION = "education"        # Education classes
    EXERCISE = "exercise"          # Yard time
    ASSOCIATION = "association"    # Social time on wing
    GYM = "gym"                    # Gym session
    VISITS = "visits"              # Visitor time
    HEALTHCARE = "healthcare"      # Medical appointments
    CHAPEL = "chapel"              # Religious services
    PROGRAMMES = "programmes"      # Rehabilitation programmes


class ScheduleEntry(BaseModel):
    """A scheduled activity for an inmate."""

    id: str
    inmate_id: str
    location_id: str
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    activity_type: ActivityType
    is_recurring: bool = True
    effective_date: date | None = None  # For one-off appointments
    source: str = "manual"  # "manual", "sync", "generated"
    source_id: str | None = None  # External system ID
    created_at: datetime
    updated_at: datetime

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: str, info) -> str:
        """Validate end_time format (allows overnight schedules like lock_up 19:00-07:00)."""
        # Note: We allow end_time <= start_time to support overnight schedules
        # E.g., lock_up from 19:00 to 07:00 next morning
        return v


class ScheduleEntryCreate(BaseModel):
    """Data for creating a schedule entry."""

    inmate_id: str
    location_id: str
    day_of_week: int = Field(ge=0, le=6, description="0=Monday, 6=Sunday")
    start_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    end_time: str = Field(pattern=r"^\d{2}:\d{2}$", description="HH:MM format")
    activity_type: ActivityType
    is_recurring: bool = True
    effective_date: date | None = None

    @field_validator("end_time")
    @classmethod
    def validate_time_range(cls, v: str, info) -> str:
        """Validate end_time format (allows overnight schedules like lock_up 19:00-07:00)."""
        # Note: We allow end_time <= start_time to support overnight schedules
        # E.g., lock_up from 19:00 to 07:00 next morning
        return v


class ScheduleEntryUpdate(BaseModel):
    """Data for updating a schedule entry (all fields optional)."""

    location_id: str | None = None
    start_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    end_time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    activity_type: ActivityType | None = None


class ScheduleQuery(BaseModel):
    """Query parameters for schedule lookups."""

    inmate_id: str | None = None
    location_id: str | None = None
    day_of_week: int | None = Field(None, ge=0, le=6)
    time: str | None = Field(None, pattern=r"^\d{2}:\d{2}$")
    activity_type: ActivityType | None = None


class ScheduleSyncBatch(BaseModel):
    """Batch of schedule entries for sync from external system."""

    source: str = "sync"
    entries: list[ScheduleEntryCreate]
