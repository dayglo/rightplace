"""
Face Recognition Service.

Orchestrates face detection, embedding extraction, and matching
for enrollment and verification workflows.
"""
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
from pydantic import BaseModel

from app.config import FaceRecognitionPolicy
from app.db.repositories.embedding_repo import EmbeddingRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.ml.face_detector import FaceDetector
from app.ml.face_embedder import FaceEmbedder
from app.ml.face_matcher import FaceMatcher
from app.models.face import DetectionResult, MatchResult, QualityIssue
from app.models.inmate import InmateUpdate

logger = logging.getLogger(__name__)


class EnrollmentResult(BaseModel):
    """Result of face enrollment operation."""

    success: bool
    inmate_id: str
    quality: float
    enrolled_at: datetime | None = None
    message: str
    quality_issues: list[QualityIssue]


class FaceRecognitionService:
    """
    Face recognition service orchestrating ML components.
    
    This service provides high-level methods for face detection,
    enrollment, and verification by coordinating the FaceDetector,
    FaceEmbedder, and FaceMatcher components.
    """

    def __init__(
        self,
        detector: FaceDetector,
        embedder: FaceEmbedder,
        matcher: FaceMatcher,
        inmate_repo: InmateRepository,
        embedding_repo: EmbeddingRepository,
        policy: FaceRecognitionPolicy,
    ):
        """
        Initialize face recognition service.
        
        Args:
            detector: Face detector instance
            embedder: Face embedder instance
            matcher: Face matcher instance
            inmate_repo: Inmate repository instance
            embedding_repo: Embedding repository instance
            policy: Face recognition policy configuration
        """
        self.detector = detector
        self.embedder = embedder
        self.matcher = matcher
        self.inmate_repo = inmate_repo
        self.embedding_repo = embedding_repo
        self.policy = policy
        
        logger.info("Initialized FaceRecognitionService")

    def detect_face(self, image_path: str | Path) -> DetectionResult:
        """
        Detect face in an image.
        
        This is a convenience wrapper around the FaceDetector.
        
        Args:
            image_path: Path to image file
            
        Returns:
            DetectionResult with detection info and quality assessment
        """
        logger.debug(f"Detecting face in {image_path}")
        result = self.detector.detect(image_path)
        
        if result.detected:
            logger.info(
                f"Face detected with quality {result.quality:.2f}, "
                f"issues: {[issue.value for issue in result.quality_issues]}"
            )
        else:
            logger.warning(f"No face detected in {image_path}")
        
        return result

    def enroll_face(
        self, inmate_id: str, image_path: str | Path
    ) -> EnrollmentResult:
        """
        Enroll a face for an inmate.
        
        This performs the complete enrollment workflow:
        1. Check if inmate exists
        2. Detect face in image
        3. Check quality against enrollment threshold
        4. Extract face embedding
        5. Store embedding in database
        6. Update inmate record
        
        Args:
            inmate_id: Inmate ID
            image_path: Path to enrollment image
            
        Returns:
            EnrollmentResult with success status and details
        """
        logger.info(f"Starting enrollment for inmate {inmate_id}")
        
        # Check if inmate exists
        inmate = self.inmate_repo.get_by_id(inmate_id)
        if inmate is None:
            logger.error(f"Inmate {inmate_id} not found")
            return EnrollmentResult(
                success=False,
                inmate_id=inmate_id,
                quality=0.0,
                enrolled_at=None,
                message=f"Inmate {inmate_id} not found",
                quality_issues=[],
            )
        
        # Detect face
        detection = self.detector.detect(image_path)
        
        # Check if face was detected
        if not detection.detected:
            logger.warning(f"No face detected for inmate {inmate_id}")
            return EnrollmentResult(
                success=False,
                inmate_id=inmate_id,
                quality=detection.quality,
                enrolled_at=None,
                message="No face detected in image",
                quality_issues=detection.quality_issues,
            )
        
        # Check quality against enrollment threshold
        if detection.quality < self.policy.enrollment_quality_threshold:
            logger.warning(
                f"Image quality {detection.quality:.2f} below enrollment "
                f"threshold {self.policy.enrollment_quality_threshold:.2f}"
            )
            return EnrollmentResult(
                success=False,
                inmate_id=inmate_id,
                quality=detection.quality,
                enrolled_at=None,
                message=(
                    f"Image quality {detection.quality:.2f} below "
                    f"threshold {self.policy.enrollment_quality_threshold:.2f}"
                ),
                quality_issues=detection.quality_issues,
            )
        
        # Extract embedding
        logger.debug(f"Extracting embedding for inmate {inmate_id}")
        embedding = self.embedder.extract(image_path)
        
        # Store embedding
        logger.debug(f"Storing embedding for inmate {inmate_id}")
        self.embedding_repo.save(
            inmate_id=inmate_id,
            embedding=embedding,
            model_version=self.embedder.model_name,
        )
        
        # Update inmate record
        now = datetime.now()
        self.inmate_repo.update(
            inmate_id=inmate_id,
            update_data=InmateUpdate(),
            is_enrolled=True,
            enrolled_at=now,
        )
        
        logger.info(
            f"Successfully enrolled inmate {inmate_id} with quality {detection.quality:.2f}"
        )
        
        return EnrollmentResult(
            success=True,
            inmate_id=inmate_id,
            quality=detection.quality,
            enrolled_at=now,
            message="Enrollment successful",
            quality_issues=detection.quality_issues,
        )

    def verify_face(
        self,
        image_path: str | Path,
        location_id: str | None = None,
    ) -> MatchResult:
        """
        Verify a face against enrolled inmates.
        
        This performs the complete verification workflow:
        1. Detect face in image
        2. Extract face embedding
        3. Match against enrolled inmates
        4. Return match result with recommendation
        
        Args:
            image_path: Path to verification image
            location_id: Optional location ID for location checking
            
        Returns:
            MatchResult with match info, confidence, and recommendation
        """
        logger.info("Starting face verification")
        
        # Detect face
        detection = self.detector.detect(image_path)
        
        # If no face detected, return no match result
        if not detection.detected:
            logger.warning("No face detected during verification")
            return MatchResult(
                matched=False,
                inmate_id=None,
                inmate=None,
                confidence=0.0,
                threshold_used=self.policy.verification_threshold,
                recommendation=self.matcher.get_recommendation(0.0),
                at_expected_location=None,
                all_matches=[],
                detection=detection,
            )
        
        # Extract embedding
        logger.debug("Extracting embedding from verification image")
        embedding = self.embedder.extract(image_path)
        
        # Get all enrolled embeddings
        enrolled_embeddings = self.embedding_repo.get_all()
        
        if not enrolled_embeddings:
            logger.warning("No enrolled inmates to match against")
            return MatchResult(
                matched=False,
                inmate_id=None,
                inmate=None,
                confidence=0.0,
                threshold_used=self.policy.verification_threshold,
                recommendation=self.matcher.get_recommendation(0.0),
                at_expected_location=None,
                all_matches=[],
                detection=detection,
            )
        
        # Find match
        logger.debug(f"Matching against {len(enrolled_embeddings)} enrolled inmates")
        match_result = self.matcher.find_match(embedding, enrolled_embeddings)
        
        # Populate detection in result
        match_result.detection = detection
        
        # If matched, populate inmate details
        if match_result.matched and match_result.inmate_id:
            inmate = self.inmate_repo.get_by_id(match_result.inmate_id)
            match_result.inmate = inmate
            
            logger.info(
                f"Matched inmate {match_result.inmate_id} with "
                f"confidence {match_result.confidence:.2f} "
                f"(recommendation: {match_result.recommendation.value})"
            )
        else:
            logger.info(
                f"No match found (best confidence: {match_result.confidence:.2f})"
            )
        
        return match_result
