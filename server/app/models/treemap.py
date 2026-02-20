"""
Treemap data models.

Defines models for hierarchical treemap visualization of rollcall status.
"""
from typing import Dict, List, Optional

from pydantic import BaseModel

from app.models.location import LocationType


class InmateVerification(BaseModel):
    """Inmate verification details for tooltip display."""

    inmate_id: str
    name: str
    status: str  # verified, not_found, wrong_location, pending


class TreemapMetadata(BaseModel):
    """Metadata for a treemap node."""

    inmate_count: int = 0
    verified_count: int = 0
    failed_count: int = 0
    scheduled_time: Optional[str] = None
    actual_time: Optional[str] = None
    inmates: Optional[List[InmateVerification]] = None  # Prisoner details (for cells)


class TreemapNode(BaseModel):
    """Node in the treemap hierarchy."""

    id: Optional[str] = None
    name: str
    type: str  # root, prison, houseblock, wing, landing, cell
    value: int  # Size of the rectangle (inmate count)
    status: str  # grey, amber, green, red
    children: Optional[List["TreemapNode"]] = None
    metadata: Optional[TreemapMetadata] = None


class TreemapResponse(BaseModel):
    """Response containing treemap hierarchy."""

    name: str
    type: str
    value: int
    children: List[TreemapNode]


class TreemapBatchRequest(BaseModel):
    """Request for batch treemap data at multiple timestamps."""

    timestamps: List[str]  # ISO format timestamps
    prison_ids: Optional[List[str]] = None
    rollcall_ids: Optional[List[str]] = None
    include_empty: bool = False
    occupancy_mode: str = "scheduled"


class TreemapBatchResponse(BaseModel):
    """Response containing treemap data for multiple timestamps."""

    data: Dict[str, TreemapResponse]
