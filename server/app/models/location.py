"""
Location data models.

Defines models for facility locations with hierarchical structure.
"""
from enum import Enum

from pydantic import BaseModel


class LocationType(str, Enum):
    """Types of locations in the facility (UK prison terminology)."""

    # Hierarchical accommodation
    HOUSEBLOCK = "houseblock"      # Top-level building (e.g., "Houseblock 1")
    WING = "wing"                   # Section within houseblock (e.g., "A Wing")
    LANDING = "landing"             # Floor within wing (e.g., "1s", "2s", "3s")
    CELL = "cell"                   # Individual cell (e.g., "A1-01")
    
    # Special units
    HEALTHCARE = "healthcare"       # Healthcare Unit
    SEGREGATION = "segregation"     # Close Supervision Centre (CSU)
    VPU = "vpu"                     # Vulnerable Prisoner Unit
    INDUCTION = "induction"         # Induction Unit
    
    # Facilities
    EDUCATION = "education"         # Education Block
    WORKSHOP = "workshop"           # Workshops
    GYM = "gym"                     # Gymnasium
    CHAPEL = "chapel"               # Chapel/Multi-faith room
    VISITS = "visits"               # Visits Hall
    RECEPTION = "reception"         # Reception area
    KITCHEN = "kitchen"             # Kitchen
    YARD = "yard"                   # Exercise yard
    ADMIN = "admin"                 # Admin offices


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
    x_coord: float | None = None  # Optional: for map visualization
    y_coord: float | None = None  # Optional: for map visualization


class LocationConnectionCreate(BaseModel):
    """Data required to create a location connection."""

    from_location_id: str
    to_location_id: str
    distance_meters: int = 10
    travel_time_seconds: int = 15
    connection_type: str = "corridor"  # corridor, stairwell, walkway, gate
    is_bidirectional: bool = True
    requires_escort: bool = False


class LocationConnection(BaseModel):
    """Walkable connection between two locations (for pathfinding)."""

    id: str
    from_location_id: str
    to_location_id: str
    distance_meters: int = 10
    travel_time_seconds: int = 15
    connection_type: str = "corridor"
    is_bidirectional: bool = True
    requires_escort: bool = False
