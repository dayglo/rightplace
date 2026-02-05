"""
Treemap visualization endpoint for Prison Roll Call API.

Provides hierarchical treemap data for rollcall status visualization.
"""
from datetime import datetime
from enum import Enum
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Depends, Query

from app.db.database import get_db
from app.models.treemap import TreemapResponse
from app.services.treemap_service import OccupancyMode, TreemapService

router = APIRouter()


# Dependency injection helpers
def get_treemap_service(db=Depends(get_db)) -> TreemapService:
    """Dependency to get TreemapService instance."""
    return TreemapService(db)


@router.get("/treemap", response_model=TreemapResponse)
def get_treemap(
    timestamp: str = Query(
        ...,
        description="ISO 8601 timestamp for which to show status",
        example="2024-01-15T10:30:00",
    ),
    rollcall_ids: Optional[str] = Query(
        None,
        description="Comma-separated list of rollcall IDs (omit or empty = show all locations)",
        example="123,456,789",
    ),
    include_empty: bool = Query(
        False,
        description="Include locations with no inmates",
    ),
    occupancy_mode: OccupancyMode = Query(
        OccupancyMode.SCHEDULED,
        description="How to determine inmate locations: 'scheduled' uses schedule data, 'home_cell' uses static assignments",
    ),
    treemap_service: TreemapService = Depends(get_treemap_service),
) -> TreemapResponse:
    """
    Get hierarchical treemap data for rollcall visualization.

    Returns a tree structure showing verification status across the prison
    hierarchy at a specific point in time.

    **Query Parameters:**
    - timestamp: ISO 8601 timestamp for which to show status (required)
    - rollcall_ids: Comma-separated list of rollcall IDs (optional, empty = show all locations)
    - include_empty: Include locations with no inmates (default: false)
    - occupancy_mode: How to determine where inmates are (default: scheduled)
      - 'scheduled': Use schedule data to show where inmates should be at the timestamp
      - 'home_cell': Use static home cell assignments (inmates always in their cell)

    **Usage:**
    - With rollcalls: Shows status in context of specified rollcalls
    - Without rollcalls: Shows entire prison hierarchy with grey status (management view)
    - With include_empty: Shows all locations including empty cells
    - With occupancy_mode=scheduled: Circles scale/disappear based on who's actually there

    **Status Color Coding:**
    - Grey: Locations with prisoners but no rollcall scheduled at timestamp
    - Amber: Rollcall scheduled at timestamp but not completed
    - Green: Rollcall completed AND all prisoners verified
    - Red: Rollcall completed BUT any prisoner NOT verified

    **Response Structure:**
    - Tree hierarchy starting from prison level
    - Each node has: id, name, type, value (inmate count), status, children, metadata
    - Metadata includes: inmate_count, verified_count, failed_count, scheduled/actual time
    """
    try:
        # Parse comma-separated rollcall IDs (allow empty for "show all" mode)
        if rollcall_ids:
            rollcall_id_list = [rc_id.strip() for rc_id in rollcall_ids.split(",") if rc_id.strip()]
        else:
            rollcall_id_list = []

        # Parse timestamp
        try:
            timestamp_dt = datetime.fromisoformat(timestamp)
        except ValueError:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid timestamp format: {timestamp}. Expected ISO 8601 format.",
            )

        # Build treemap hierarchy
        treemap_data = treemap_service.build_treemap_hierarchy(
            rollcall_id_list, timestamp_dt, include_empty, occupancy_mode
        )

        return treemap_data

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to build treemap: {str(e)}",
        )
