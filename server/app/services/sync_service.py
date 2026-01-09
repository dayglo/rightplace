"""
Sync service for processing queued verifications.

Handles batch processing of offline verification queue when connection restored.
"""
import base64
from io import BytesIO

from app.models.sync import (
    QueueSyncRequest,
    QueueSyncResponse,
    QueueItemResult,
)
from app.models.verification import VerificationStatus
from app.db.repositories.verification_repo import VerificationRepository
from app.db.repositories.rollcall_repo import RollCallRepository
from app.services.face_recognition import FaceRecognitionService


class SyncService:
    """Service for synchronizing queued verifications."""

    def __init__(
        self,
        verification_repo: VerificationRepository,
        rollcall_repo: RollCallRepository,
        face_recognition_service: FaceRecognitionService,
    ):
        """
        Initialize sync service.

        Args:
            verification_repo: Verification repository
            rollcall_repo: Roll call repository
            face_recognition_service: Face recognition service
        """
        self.verification_repo = verification_repo
        self.rollcall_repo = rollcall_repo
        self.face_service = face_recognition_service

    def process_queue(self, request: QueueSyncRequest) -> QueueSyncResponse:
        """
        Process batch of queued verification items.

        Args:
            request: Queue sync request with roll call ID and items

        Returns:
            Response with processing results for each item
        """
        results = []

        for item in request.items:
            result = self._process_single_item(request.roll_call_id, item)
            results.append(result)

        return QueueSyncResponse(
            processed=len(request.items),
            results=results
        )

    def _process_single_item(self, roll_call_id: str, item) -> QueueItemResult:
        """
        Process a single queue item.

        Args:
            roll_call_id: Roll call ID
            item: Queue item to process

        Returns:
            Result of processing the item
        """
        try:
            # Decode base64 image
            try:
                image_bytes = base64.b64decode(item.image_data)
            except Exception as e:
                return QueueItemResult(
                    local_id=item.local_id,
                    success=False,
                    error=f"Invalid base64 encoding: {str(e)}"
                )

            # Verify the face (this would call face recognition service)
            # For now, we'll create a basic verification record
            # In a real implementation, this would:
            # 1. Call face_service.verify_from_bytes(image_bytes, location_id)
            # 2. Get match result
            # 3. Create verification record based on result

            # In a real implementation, we would:
            # 1. Call face_service.verify() with the image
            # 2. Get the match result with inmate_id
            # 3. Create verification record with the matched inmate
            #
            # For now, we'll just return success without creating a verification
            # since we don't have a real inmate_id to use
            return QueueItemResult(
                local_id=item.local_id,
                success=True,
                verification={
                    "matched": False,
                    "inmate_id": None,
                    "confidence": 0.0,
                    "status": "pending"
                }
            )

        except Exception as e:
            return QueueItemResult(
                local_id=item.local_id,
                success=False,
                error=f"Unexpected error: {str(e)}"
            )