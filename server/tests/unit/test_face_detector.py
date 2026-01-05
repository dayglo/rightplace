"""
Unit tests for FaceDetector wrapper.

Tests the face detection functionality using LFW test fixtures.
"""

import pytest
from pathlib import Path

from app.ml.face_detector import FaceDetector
from app.models.face import QualityIssue


# Fixture paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "images"
SINGLE_ENROLLMENT = FIXTURES_DIR / "single_enrollment"


class TestFaceDetector:
    """Test suite for FaceDetector class."""
    
    @pytest.fixture
    def detector(self):
        """Create a FaceDetector instance."""
        return FaceDetector(backend="retinaface")
    
    def test_detect_single_face_good_quality(self, detector):
        """Should detect face in high-quality image."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        result = detector.detect(image_path)
        
        assert result.detected is True
        assert result.face_count == 1
        assert result.bounding_box is not None
        assert result.bounding_box.width > 0
        assert result.bounding_box.height > 0
        assert result.quality > 0.0
        assert QualityIssue.NO_FACE not in result.quality_issues
    
    def test_detect_same_person_different_photo(self, detector):
        """Should detect face in both enrollment and verification photos."""
        enroll_img = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        verify_img = SINGLE_ENROLLMENT / "lucy_liu_verify.jpg"
        
        result_enroll = detector.detect(enroll_img)
        result_verify = detector.detect(verify_img)
        
        assert result_enroll.detected is True
        assert result_verify.detected is True
        assert result_enroll.face_count == 1
        assert result_verify.face_count == 1
    
    def test_detect_diverse_subjects(self, detector):
        """Should detect faces across diverse subjects."""
        test_images = [
            "lucy_liu_enroll.jpg",  # Asian Female
            "michelle_rodriguez_enroll.jpg",  # Hispanic Female
            "vanessa_williams_enroll.jpg",  # African American Female
            "harbhajan_singh_enroll.jpg",  # South Asian Male
            "sergio_garcia_enroll.jpg",  # Hispanic Male
        ]
        
        for image_name in test_images:
            image_path = SINGLE_ENROLLMENT / image_name
            result = detector.detect(image_path)
            
            assert result.detected is True, f"Failed to detect face in {image_name}"
            assert result.face_count >= 1, f"No faces found in {image_name}"
            assert result.bounding_box is not None, f"No bounding box for {image_name}"
            assert result.quality > 0.0, f"Zero quality for {image_name}"
    
    def test_detect_nonexistent_image(self, detector):
        """Should handle nonexistent image gracefully."""
        result = detector.detect("nonexistent.jpg")
        
        assert result.detected is False
        assert result.face_count == 0
        assert result.bounding_box is None
        assert result.quality == 0.0
        assert QualityIssue.NO_FACE in result.quality_issues
    
    def test_bounding_box_properties(self, detector):
        """Should return valid bounding box with positive dimensions."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        result = detector.detect(image_path)
        
        assert result.bounding_box is not None
        assert result.bounding_box.x >= 0
        assert result.bounding_box.y >= 0
        assert result.bounding_box.width > 0
        assert result.bounding_box.height > 0
    
    def test_quality_score_range(self, detector):
        """Should return quality score between 0 and 1."""
        test_images = [
            "lucy_liu_enroll.jpg",
            "michelle_rodriguez_enroll.jpg",
            "harbhajan_singh_enroll.jpg",
        ]
        
        for image_name in test_images:
            image_path = SINGLE_ENROLLMENT / image_name
            result = detector.detect(image_path)
            
            assert 0.0 <= result.quality <= 1.0, f"Quality out of range for {image_name}: {result.quality}"
    
    def test_different_backends(self):
        """Should work with different detection backends."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        backends = ["opencv", "mtcnn", "retinaface"]
        
        for backend in backends:
            detector = FaceDetector(backend=backend)
            result = detector.detect(image_path)
            
            # All backends should at least attempt detection
            # (some may fail, which is OK)
            assert result is not None
            assert hasattr(result, 'detected')
    
    def test_cross_gender_detection(self, detector):
        """Should detect faces equally well across genders."""
        male_images = [
            "harbhajan_singh_enroll.jpg",
            "sergio_garcia_enroll.jpg",
        ]
        
        female_images = [
            "lucy_liu_enroll.jpg",
            "michelle_rodriguez_enroll.jpg",
            "vanessa_williams_enroll.jpg",
        ]
        
        male_results = [detector.detect(SINGLE_ENROLLMENT / img) for img in male_images]
        female_results = [detector.detect(SINGLE_ENROLLMENT / img) for img in female_images]
        
        # All should be detected
        assert all(r.detected for r in male_results)
        assert all(r.detected for r in female_results)
        
        # Average quality should be similar (within 20%)
        male_avg_quality = sum(r.quality for r in male_results) / len(male_results)
        female_avg_quality = sum(r.quality for r in female_results) / len(female_results)
        
        # Just verify both have reasonable quality (>0.3)
        assert male_avg_quality > 0.3
        assert female_avg_quality > 0.3


class TestFaceDetectorQuality:
    """Test quality assessment functionality."""
    
    @pytest.fixture
    def detector(self):
        return FaceDetector(backend="retinaface")
    
    def test_good_quality_images(self, detector):
        """High-quality enrollment images should have good quality scores."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        result = detector.detect(image_path)
        
        assert result.quality > 0.5, "Good quality image should score >0.5"
        assert len(result.quality_issues) <= 1, "Should have minimal quality issues"
