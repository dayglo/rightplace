"""
Sync models for queue synchronization.

Used when mobile app syncs queued verifications after being offline.
"""
from datetime import datetime
from pydantic import BaseModel


class QueueItem(BaseModel):
    """Single item in the sync queue."""

    local_id: str  # Mobile-generated ID for tracking
    queued_at: datetime  # When it was queued on mobile
    location_id: str
    image_data: str  # base64 encoded image


class QueueSyncRequest(BaseModel):
    """Request to sync queued verifications."""

    roll_call_id: str
    items: list[QueueItem]


class QueueItemResult(BaseModel):
    """Result of processing a single queue item."""

    local_id: str
    success: bool
    verification: dict | None = None  # Verification result if success
    error: str | None = None  # Error message if failed


class QueueSyncResponse(BaseModel):
    """Response from queue sync operation."""

    processed: int
    results: list[QueueItemResult]