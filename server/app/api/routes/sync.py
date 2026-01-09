"""
Sync endpoint for queue synchronization.

Handles batch processing of queued verifications from mobile app.
"""
from fastapi import APIRouter, Depends

from app.db.database import get_db
from app.db.repositories.verification_repo import VerificationRepository
from app.db.repositories.rollcall_repo import RollCallRepository
from app.services.sync_service import SyncService
from app.services.face_recognition import FaceRecognitionService
from app.models.sync import QueueSyncRequest, QueueSyncResponse

router = APIRouter()


def get_sync_service(db=Depends(get_db)) -> SyncService:
    """Dependency to get SyncService instance."""
    from app.ml.face_detector import FaceDetector
    from app.ml.face_embedder import FaceEmbedder
    from app.ml.face_matcher import FaceMatcher
    from app.db.repositories.embedding_repo import EmbeddingRepository
    from app.config import Settings
    
    settings = Settings()
    
    verification_repo = VerificationRepository(db)
    rollcall_repo = RollCallRepository(db)
    embedding_repo = EmbeddingRepository(db)
    
    # Create face recognition service
    detector = FaceDetector(backend=settings.face_detection_backend)
    embedder = FaceEmbedder(model_name=settings.face_recognition_model)
    matcher = FaceMatcher(policy=settings.face_recognition_policy)
    
    face_service = FaceRecognitionService(
        detector=detector,
        embedder=embedder,
        matcher=matcher,
        embedding_repo=embedding_repo
    )
    
    return SyncService(
        verification_repo=verification_repo,
        rollcall_repo=rollcall_repo,
        face_recognition_service=face_service
    )


@router.post("/sync/queue", response_model=QueueSyncResponse)
async def sync_queue(
    request: QueueSyncRequest,
    service: SyncService = Depends(get_sync_service),
):
    """
    Sync queued verifications from mobile app.
    
    When mobile app was offline, verifications were queued locally.
    This endpoint processes the entire queue in batch.
    
    Args:
        request: Queue sync request with roll call ID and items
        
    Returns:
        QueueSyncResponse with results for each item
    """
    return service.process_queue(request)