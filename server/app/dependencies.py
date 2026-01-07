"""
Dependency injection helpers for FastAPI.

Provides factory functions for creating and managing service instances.
"""
from functools import lru_cache

from app.config import Settings
from app.db.database import get_db
from app.db.repositories.embedding_repo import EmbeddingRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.ml.face_detector import FaceDetector
from app.ml.face_embedder import FaceEmbedder
from app.ml.face_matcher import FaceMatcher
from app.services.face_recognition import FaceRecognitionService


@lru_cache()
def get_settings() -> Settings:
    """Get singleton Settings instance."""
    return Settings()


@lru_cache()
def get_face_detector() -> FaceDetector:
    """Get singleton FaceDetector instance."""
    # Use default backend (retinaface)
    return FaceDetector(backend="retinaface")


@lru_cache()
def get_face_embedder() -> FaceEmbedder:
    """Get singleton FaceEmbedder instance."""
    # Use default model (Facenet512)
    return FaceEmbedder(model="Facenet512")


@lru_cache()
def get_face_matcher() -> FaceMatcher:
    """Get singleton FaceMatcher instance."""
    settings = get_settings()
    policy = settings.policy
    return FaceMatcher(
        threshold=policy.verification_threshold,
        auto_accept_threshold=policy.auto_accept_threshold,
        review_threshold=policy.manual_review_threshold
    )


def get_face_recognition_service(
    db=None,
) -> FaceRecognitionService:
    """
    Get FaceRecognitionService instance.
    
    Note: Not cached because it depends on database connection which
    should be created per request.
    
    Args:
        db: Database connection (optional, will create if None)
        
    Returns:
        FaceRecognitionService instance
    """
    settings = get_settings()
    
    # Get ML components (cached singletons)
    detector = get_face_detector()
    embedder = get_face_embedder()
    matcher = get_face_matcher()
    
    # Get or create database connection
    if db is None:
        db = next(get_db())
    
    # Create repositories
    inmate_repo = InmateRepository(db)
    embedding_repo = EmbeddingRepository(db)
    
    return FaceRecognitionService(
        detector=detector,
        embedder=embedder,
        matcher=matcher,
        inmate_repo=inmate_repo,
        embedding_repo=embedding_repo,
        policy=settings.policy,
    )
