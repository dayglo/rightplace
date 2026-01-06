"""
Test suite for Face Recognition Service.

Tests the FaceRecognitionService which orchestrates face detection,
embedding extraction, and matching for enrollment and verification workflows.
"""
import pytest
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, MagicMock
import numpy as np

from app.services.face_recognition import FaceRecognitionService, EnrollmentResult
from app.models.face import (
    DetectionResult,
    MatchResult,
    MatchRecommendation,
    QualityIssue,
    BoundingBox,
)
from app.models.inmate import Inmate
from app.config import FaceRecognitionPolicy


@pytest.fixture
def policy():
    """Standard policy configuration."""
    return FaceRecognitionPolicy(
        verification_threshold=0.75,
        enrollment_quality_threshold=0.80,
        auto_accept_threshold=0.92,
        manual_review_threshold=0.60,
    )


@pytest.fixture
def mock_detector():
    """Mock FaceDetector."""
    detector = Mock()
    return detector


@pytest.fixture
def mock_embedder():
    """Mock FaceEmbedder."""
    embedder = Mock()
    return embedder


@pytest.fixture
def mock_matcher():
    """Mock FaceMatcher."""
    matcher = Mock()
    return matcher


@pytest.fixture
def mock_inmate_repo():
    """Mock InmateRepository."""
    repo = Mock()
    return repo


@pytest.fixture
def mock_embedding_repo():
    """Mock EmbeddingRepository."""
    repo = Mock()
    return repo


@pytest.fixture
def service(
    mock_detector,
    mock_embedder,
    mock_matcher,
    mock_inmate_repo,
    mock_embedding_repo,
    policy,
):
    """FaceRecognitionService with mocked dependencies."""
    return FaceRecognitionService(
        detector=mock_detector,
        embedder=mock_embedder,
        matcher=mock_matcher,
        inmate_repo=mock_inmate_repo,
        embedding_repo=mock_embedding_repo,
        policy=policy,
    )


@pytest.fixture
def sample_inmate():
    """Sample inmate for testing."""
    return Inmate(
        id="inmate-123",
        inmate_number="A12345",
        first_name="John",
        last_name="Doe",
        date_of_birth="1990-01-01",
        cell_block="A",
        cell_number="101",
        photo_uri=None,
        is_enrolled=False,
        enrolled_at=None,
        is_active=True,
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )


@pytest.fixture
def high_quality_detection():
    """High quality face detection result."""
    return DetectionResult(
        detected=True,
        face_count=1,
        bounding_box=BoundingBox(x=100, y=100, width=200, height=200),
        landmarks=None,
        quality=0.92,
        quality_issues=[],
    )


@pytest.fixture
def low_quality_detection():
    """Low quality face detection result."""
    return DetectionResult(
        detected=True,
        face_count=1,
        bounding_box=BoundingBox(x=100, y=100, width=200, height=200),
        landmarks=None,
        quality=0.45,
        quality_issues=[QualityIssue.BLUR, QualityIssue.LOW_LIGHT],
    )


@pytest.fixture
def no_face_detection():
    """No face detected result."""
    return DetectionResult(
        detected=False,
        face_count=0,
        bounding_box=None,
        landmarks=None,
        quality=0.0,
        quality_issues=[QualityIssue.NO_FACE],
    )


@pytest.fixture
def sample_embedding():
    """Sample face embedding vector."""
    return np.random.rand(512).astype(np.float32)


class TestDetection:
    """Test face detection functionality."""

    def test_detect_face_valid_image_returns_detection(
        self, service, mock_detector, high_quality_detection
    ):
        """Should detect face in valid image."""
        mock_detector.detect.return_value = high_quality_detection
        
        result = service.detect_face("image.jpg")
        
        assert result.detected is True
        assert result.quality == 0.92
        assert len(result.quality_issues) == 0
        mock_detector.detect.assert_called_once_with("image.jpg")

    def test_detect_face_no_face_returns_no_detection(
        self, service, mock_detector, no_face_detection
    ):
        """Should return no detection when no face found."""
        mock_detector.detect.return_value = no_face_detection
        
        result = service.detect_face("no_face.jpg")
        
        assert result.detected is False
        assert result.face_count == 0
        assert QualityIssue.NO_FACE in result.quality_issues

    def test_detect_face_multiple_faces_flags_issue(self, service, mock_detector):
        """Should flag when multiple faces detected."""
        multi_face_detection = DetectionResult(
            detected=True,
            face_count=2,
            bounding_box=BoundingBox(x=100, y=100, width=200, height=200),
            landmarks=None,
            quality=0.85,
            quality_issues=[QualityIssue.MULTI_FACE],
        )
        mock_detector.detect.return_value = multi_face_detection
        
        result = service.detect_face("multi_face.jpg")
        
        assert result.detected is True
        assert result.face_count == 2
        assert QualityIssue.MULTI_FACE in result.quality_issues


class TestEnrollment:
    """Test face enrollment functionality."""

    def test_enroll_face_high_quality_succeeds(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_inmate_repo,
        mock_embedding_repo,
        sample_inmate,
        high_quality_detection,
        sample_embedding,
    ):
        """Should enroll face when quality is high enough."""
        # Setup mocks
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_inmate_repo.get_by_id.return_value = sample_inmate
        mock_inmate_repo.update.return_value = sample_inmate
        
        result = service.enroll_face("inmate-123", "image.jpg")
        
        assert result.success is True
        assert result.inmate_id == "inmate-123"
        assert result.quality == 0.92
        assert len(result.quality_issues) == 0
        
        # Verify embedding was stored
        mock_embedding_repo.save.assert_called_once()
        
        # Verify inmate was updated
        mock_inmate_repo.update.assert_called_once()

    def test_enroll_face_low_quality_fails(
        self,
        service,
        mock_detector,
        mock_inmate_repo,
        sample_inmate,
        low_quality_detection,
    ):
        """Should reject enrollment when quality too low."""
        mock_detector.detect.return_value = low_quality_detection
        mock_inmate_repo.get_by_id.return_value = sample_inmate
        
        result = service.enroll_face("inmate-123", "low_quality.jpg")
        
        assert result.success is False
        assert result.quality == 0.45
        assert QualityIssue.BLUR in result.quality_issues
        assert "quality" in result.message.lower()

    def test_enroll_face_no_face_fails(
        self,
        service,
        mock_detector,
        mock_inmate_repo,
        sample_inmate,
        no_face_detection,
    ):
        """Should fail enrollment when no face detected."""
        mock_detector.detect.return_value = no_face_detection
        mock_inmate_repo.get_by_id.return_value = sample_inmate
        
        result = service.enroll_face("inmate-123", "no_face.jpg")
        
        assert result.success is False
        assert result.quality == 0.0
        assert QualityIssue.NO_FACE in result.quality_issues

    def test_enroll_face_nonexistent_inmate_fails(
        self, service, mock_inmate_repo
    ):
        """Should fail when inmate doesn't exist."""
        mock_inmate_repo.get_by_id.return_value = None
        
        result = service.enroll_face("nonexistent", "image.jpg")
        
        assert result.success is False
        assert "not found" in result.message.lower()

    def test_enroll_face_updates_inmate_record(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_inmate_repo,
        mock_embedding_repo,
        sample_inmate,
        high_quality_detection,
        sample_embedding,
    ):
        """Should update inmate is_enrolled and enrolled_at fields."""
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_inmate_repo.get_by_id.return_value = sample_inmate
        mock_inmate_repo.update.return_value = sample_inmate
        
        result = service.enroll_face("inmate-123", "image.jpg")
        
        # Verify update was called with enrollment fields
        call_args = mock_inmate_repo.update.call_args
        assert call_args[1]["is_enrolled"] is True
        assert call_args[1]["enrolled_at"] is not None

    def test_enroll_face_stores_embedding(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_inmate_repo,
        mock_embedding_repo,
        sample_inmate,
        high_quality_detection,
        sample_embedding,
    ):
        """Should store embedding in repository."""
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_inmate_repo.get_by_id.return_value = sample_inmate
        
        service.enroll_face("inmate-123", "image.jpg")
        
        # Verify embedding was saved with correct parameters (using kwargs)
        mock_embedding_repo.save.assert_called_once()
        call_kwargs = mock_embedding_repo.save.call_args[1]
        assert call_kwargs["inmate_id"] == "inmate-123"
        assert np.array_equal(call_kwargs["embedding"], sample_embedding)


class TestVerification:
    """Test face verification functionality."""

    def test_verify_face_enrolled_inmate_matches(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_matcher,
        mock_embedding_repo,
        high_quality_detection,
        sample_embedding,
        sample_inmate,
    ):
        """Should match enrolled inmate with high confidence."""
        # Setup mocks
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_embedding_repo.get_all.return_value = {"inmate-123": sample_embedding}
        
        match_result = MatchResult(
            matched=True,
            inmate_id="inmate-123",
            inmate=sample_inmate,
            confidence=0.89,
            threshold_used=0.75,
            recommendation=MatchRecommendation.CONFIRM,
            at_expected_location=None,
            all_matches=[{"inmate_id": "inmate-123", "confidence": 0.89}],
            detection=high_quality_detection,
        )
        mock_matcher.find_match.return_value = match_result
        
        result = service.verify_face("image.jpg")
        
        assert result.matched is True
        assert result.inmate_id == "inmate-123"
        assert result.confidence == 0.89

    def test_verify_face_no_match_returns_no_match(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_matcher,
        mock_embedding_repo,
        high_quality_detection,
        sample_embedding,
    ):
        """Should return no match when confidence below threshold."""
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_embedding_repo.get_all.return_value = {"inmate-123": np.random.rand(512)}
        
        no_match_result = MatchResult(
            matched=False,
            inmate_id=None,
            inmate=None,
            confidence=0.42,
            threshold_used=0.75,
            recommendation=MatchRecommendation.NO_MATCH,
            at_expected_location=None,
            all_matches=[],
            detection=high_quality_detection,
        )
        mock_matcher.find_match.return_value = no_match_result
        
        result = service.verify_face("image.jpg")
        
        assert result.matched is False
        assert result.inmate_id is None
        assert result.confidence == 0.42

    def test_verify_face_high_confidence_auto_accept(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_matcher,
        mock_embedding_repo,
        high_quality_detection,
        sample_embedding,
        sample_inmate,
    ):
        """Should recommend auto-accept for very high confidence."""
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_embedding_repo.get_all.return_value = {"inmate-123": sample_embedding}
        
        match_result = MatchResult(
            matched=True,
            inmate_id="inmate-123",
            inmate=sample_inmate,
            confidence=0.95,
            threshold_used=0.75,
            recommendation=MatchRecommendation.AUTO_ACCEPT,
            at_expected_location=None,
            all_matches=[{"inmate_id": "inmate-123", "confidence": 0.95}],
            detection=high_quality_detection,
        )
        mock_matcher.find_match.return_value = match_result
        
        result = service.verify_face("image.jpg")
        
        assert result.recommendation == MatchRecommendation.AUTO_ACCEPT
        assert result.confidence >= 0.92

    def test_verify_face_medium_confidence_confirm(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_matcher,
        mock_embedding_repo,
        high_quality_detection,
        sample_embedding,
        sample_inmate,
    ):
        """Should recommend confirmation for medium confidence."""
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_embedding_repo.get_all.return_value = {"inmate-123": sample_embedding}
        
        match_result = MatchResult(
            matched=True,
            inmate_id="inmate-123",
            inmate=sample_inmate,
            confidence=0.82,
            threshold_used=0.75,
            recommendation=MatchRecommendation.CONFIRM,
            at_expected_location=None,
            all_matches=[{"inmate_id": "inmate-123", "confidence": 0.82}],
            detection=high_quality_detection,
        )
        mock_matcher.find_match.return_value = match_result
        
        result = service.verify_face("image.jpg")
        
        assert result.recommendation == MatchRecommendation.CONFIRM
        assert 0.75 <= result.confidence < 0.92

    def test_verify_face_low_confidence_review(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_matcher,
        mock_embedding_repo,
        high_quality_detection,
        sample_embedding,
        sample_inmate,
    ):
        """Should recommend review for low confidence."""
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_embedding_repo.get_all.return_value = {"inmate-123": sample_embedding}
        
        match_result = MatchResult(
            matched=False,
            inmate_id=None,
            inmate=None,
            confidence=0.68,
            threshold_used=0.75,
            recommendation=MatchRecommendation.REVIEW,
            at_expected_location=None,
            all_matches=[{"inmate_id": "inmate-123", "confidence": 0.68}],
            detection=high_quality_detection,
        )
        mock_matcher.find_match.return_value = match_result
        
        result = service.verify_face("image.jpg")
        
        assert result.recommendation == MatchRecommendation.REVIEW
        assert 0.60 <= result.confidence < 0.75

    def test_verify_face_no_face_detected_returns_no_match(
        self, service, mock_detector, mock_matcher, no_face_detection
    ):
        """Should return no match result when no face detected."""
        mock_detector.detect.return_value = no_face_detection
        mock_matcher.get_recommendation.return_value = MatchRecommendation.NO_MATCH
        
        result = service.verify_face("no_face.jpg")
        
        assert result.matched is False
        assert result.detection.detected is False
        assert QualityIssue.NO_FACE in result.detection.quality_issues


class TestIntegration:
    """Test end-to-end integration scenarios."""

    def test_end_to_end_enrollment_then_verification(
        self,
        service,
        mock_detector,
        mock_embedder,
        mock_matcher,
        mock_inmate_repo,
        mock_embedding_repo,
        sample_inmate,
        high_quality_detection,
        sample_embedding,
    ):
        """Should enroll and then successfully verify same person."""
        # Enrollment
        mock_detector.detect.return_value = high_quality_detection
        mock_embedder.extract.return_value = sample_embedding
        mock_inmate_repo.get_by_id.return_value = sample_inmate
        mock_inmate_repo.update.return_value = sample_inmate
        
        enroll_result = service.enroll_face("inmate-123", "enroll.jpg")
        assert enroll_result.success is True
        
        # Verification
        mock_embedding_repo.get_all.return_value = {"inmate-123": sample_embedding}
        
        match_result = MatchResult(
            matched=True,
            inmate_id="inmate-123",
            inmate=sample_inmate,
            confidence=0.99,
            threshold_used=0.75,
            recommendation=MatchRecommendation.AUTO_ACCEPT,
            at_expected_location=None,
            all_matches=[{"inmate_id": "inmate-123", "confidence": 0.99}],
            detection=high_quality_detection,
        )
        mock_matcher.find_match.return_value = match_result
        
        verify_result = service.verify_face("verify.jpg")
        
        assert verify_result.matched is True
        assert verify_result.inmate_id == "inmate-123"
        assert verify_result.recommendation == MatchRecommendation.AUTO_ACCEPT
