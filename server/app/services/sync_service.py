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
        import tempfile
        import os
        
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

            # Save image bytes to temporary file for face recognition
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as temp_file:
                temp_file.write(image_bytes)
                temp_path = temp_file.name
            
            try:
                # Call face recognition service to verify the face
                match_result = self.face_service.verify_face(
                    image_path=temp_path,
                    location_id=item.location_id
                )
                
                # If matched, create verification record
                if match_result.matched and match_result.inmate_id:
                    verification = self.verification_repo.create(
                        roll_call_id=roll_call_id,
                        inmate_id=match_result.inmate_id,
                        location_id=item.location_id,
                        status=VerificationStatus.VERIFIED,
                        confidence=match_result.confidence,
                        is_manual_override=False,
                    )
                    
                    return QueueItemResult(
                        local_id=item.local_id,
                        success=True,
                        verification={
                            "matched": True,
                            "inmate_id": match_result.inmate_id,
                            "confidence": match_result.confidence,
                            "status": "verified",
                            "recommendation": match_result.recommendation.value
                        }
                    )
                else:
                    # No match found
                    return QueueItemResult(
                        local_id=item.local_id,
                        success=True,
                        verification={
                            "matched": False,
                            "inmate_id": None,
                            "confidence": match_result.confidence,
                            "status": "not_found",
                            "recommendation": match_result.recommendation.value
                        }
                    )
            finally:
                # Clean up temporary file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            return QueueItemResult(
                local_id=item.local_id,
                success=False,
                error=f"Unexpected error: {str(e)}"
            )
