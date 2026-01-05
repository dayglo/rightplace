"""
Location data models.

Defines models for facility locations with hierarchical structure.
"""
from enum import Enum

from pydantic import BaseModel


class LocationType(str, Enum):
    """Types of locations in the facility."""

    BLOCK = "block"
    CELL = "cell"
    COMMON_AREA = "common_area"
    YARD = "yard"
    MEDICAL = "medical"
    ADMIN = "admin"


class LocationCreate(BaseModel):
    """Data required to create a new location."""

    name: str
    type: LocationType
    parent_id: str | None = None
    capacity: int = 1
    floor: int = 0
    building: str


class LocationUpdate(BaseModel):
    """Data for updating an existing location (all fields optional)."""

    name: str | None = None
    type: LocationType | None = None
    parent_id: str | None = None
    capacity: int | None = None
    floor: int | None = None
    building: str | None = None


class Location(BaseModel):
    """Facility location with optional hierarchy."""

    id: str
    name: str
    type: LocationType
    parent_id: str | None = None
    capacity: int = 1
    floor: int = 0
    building: str
