"""
Unit tests for FaceMatcher class.

Tests the face matching functionality using cosine similarity
and validates against DeepFace's verification methods.
"""

import numpy as np
import pytest
from pathlib import Path

from app.ml.face_matcher import FaceMatcher
from app.ml.face_embedder import FaceEmbedder
from app.models.face import MatchRecommendation


# Fixture paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "images"
SINGLE_ENROLLMENT = FIXTURES_DIR / "single_enrollment"


class TestFaceMatcherSimilarity:
    """Test cosine similarity calculation."""
    
    @pytest.fixture
    def matcher(self):
        """Create a FaceMatcher instance."""
        return FaceMatcher(threshold=0.75)
    
    def test_identical_embeddings_similarity_one(self, matcher):
        """Should return similarity ~1.0 for identical embeddings."""
        emb = np.random.rand(512).astype(np.float32)
        emb = emb / np.linalg.norm(emb)  # Normalize
        
        similarity = matcher.calculate_similarity(emb, emb)
        
        assert abs(similarity - 1.0) < 0.01, f"Expected ~1.0, got {similarity}"
    
    def test_orthogonal_embeddings_similarity_zero(self, matcher):
        """Should return similarity ~0.0 for orthogonal embeddings."""
        # Create two orthogonal vectors
        emb1 = np.zeros(512, dtype=np.float32)
        emb1[0] = 1.0
        
        emb2 = np.zeros(512, dtype=np.float32)
        emb2[1] = 1.0
        
        similarity = matcher.calculate_similarity(emb1, emb2)
        
        assert abs(similarity - 0.0) < 0.01, f"Expected ~0.0, got {similarity}"
    
    def test_similarity_is_symmetric(self, matcher):
        """Should return same similarity regardless of order."""
        emb1 = np.random.rand(512).astype(np.float32)
        emb2 = np.random.rand(512).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = emb2 / np.linalg.norm(emb2)
        
        sim1 = matcher.calculate_similarity(emb1, emb2)
        sim2 = matcher.calculate_similarity(emb2, emb1)
        
        assert abs(sim1 - sim2) < 0.0001, "Similarity should be symmetric"
    
    def test_similarity_range(self, matcher):
        """Should return similarity in range [-1, 1]."""
        emb1 = np.random.rand(512).astype(np.float32)
        emb2 = np.random.rand(512).astype(np.float32)
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = emb2 / np.linalg.norm(emb2)
        
        similarity = matcher.calculate_similarity(emb1, emb2)
        
        assert -1.0 <= similarity <= 1.0, f"Similarity out of range: {similarity}"


class TestFaceMatcherRecommendations:
    """Test recommendation logic based on confidence thresholds."""
    
    @pytest.fixture
    def matcher(self):
        return FaceMatcher(
            threshold=0.75,
            auto_accept_threshold=0.92,
            review_threshold=0.60
        )
    
    def test_high_confidence_auto_accept(self, matcher):
        """Should recommend AUTO_ACCEPT for confidence ≥0.92."""
        recommendation = matcher.get_recommendation(0.95)
        assert recommendation == MatchRecommendation.AUTO_ACCEPT
        
        recommendation = matcher.get_recommendation(0.92)
        assert recommendation == MatchRecommendation.AUTO_ACCEPT
    
    def test_medium_confidence_confirm(self, matcher):
        """Should recommend CONFIRM for confidence 0.75-0.91."""
        recommendation = matcher.get_recommendation(0.85)
        assert recommendation == MatchRecommendation.CONFIRM
        
        recommendation = matcher.get_recommendation(0.75)
        assert recommendation == MatchRecommendation.CONFIRM
        
        recommendation = matcher.get_recommendation(0.91)
        assert recommendation == MatchRecommendation.CONFIRM
    
    def test_low_confidence_review(self, matcher):
        """Should recommend REVIEW for confidence 0.60-0.74."""
        recommendation = matcher.get_recommendation(0.65)
        assert recommendation == MatchRecommendation.REVIEW
        
        recommendation = matcher.get_recommendation(0.60)
        assert recommendation == MatchRecommendation.REVIEW
        
        recommendation = matcher.get_recommendation(0.74)
        assert recommendation == MatchRecommendation.REVIEW
    
    def test_very_low_confidence_no_match(self, matcher):
        """Should recommend NO_MATCH for confidence <0.60."""
        recommendation = matcher.get_recommendation(0.50)
        assert recommendation == MatchRecommendation.NO_MATCH
        
        recommendation = matcher.get_recommendation(0.59)
        assert recommendation == MatchRecommendation.NO_MATCH


class TestFaceMatcherMatching:
    """Test 1:N matching functionality."""
    
    @pytest.fixture
    def matcher(self):
        return FaceMatcher(threshold=0.75)
    
    @pytest.fixture
    def sample_embeddings(self):
        """Create sample normalized embeddings."""
        emb1 = np.random.rand(512).astype(np.float32)
        emb2 = np.random.rand(512).astype(np.float32)
        emb3 = np.random.rand(512).astype(np.float32)
        
        # Normalize
        emb1 = emb1 / np.linalg.norm(emb1)
        emb2 = emb2 / np.linalg.norm(emb2)
        emb3 = emb3 / np.linalg.norm(emb3)
        
        return {
            "inmate_001": emb1,
            "inmate_002": emb2,
            "inmate_003": emb3,
        }
    
    def test_match_above_threshold_returns_matched(self, matcher):
        """Should return matched=True when similarity above threshold."""
        query = np.random.rand(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Create a very similar embedding (high similarity)
        enrolled = query + np.random.rand(512).astype(np.float32) * 0.01
        enrolled = enrolled / np.linalg.norm(enrolled)
        
        enrolled_db = {"inmate_001": enrolled}
        result = matcher.find_match(query, enrolled_db)
        
        assert result.matched is True
        assert result.inmate_id == "inmate_001"
        assert result.confidence > 0.75
    
    def test_match_below_threshold_returns_no_match(self, matcher):
        """Should return matched=False when no similarity above threshold."""
        query = np.random.rand(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Create very different embeddings (low similarity)
        enrolled1 = np.random.rand(512).astype(np.float32)
        enrolled2 = np.random.rand(512).astype(np.float32)
        enrolled1 = enrolled1 / np.linalg.norm(enrolled1)
        enrolled2 = enrolled2 / np.linalg.norm(enrolled2)
        
        enrolled_db = {
            "inmate_001": enrolled1,
            "inmate_002": enrolled2,
        }
        
        result = matcher.find_match(query, enrolled_db)
        
        # Might match or not depending on random embeddings
        # But if no match, should return matched=False
        if result.confidence < 0.75:
            assert result.matched is False
            assert result.inmate_id is None
    
    def test_returns_best_match_from_multiple(self, matcher, sample_embeddings):
        """Should return the best match when multiple candidates exist."""
        query = sample_embeddings["inmate_002"]
        
        result = matcher.find_match(query, sample_embeddings)
        
        assert result.matched is True
        assert result.inmate_id == "inmate_002"
        assert result.confidence > 0.99  # Should be very high (almost identical)
    
    def test_returns_all_matches_ranked(self, matcher, sample_embeddings):
        """Should return all matches ranked by confidence."""
        query = sample_embeddings["inmate_001"]
        
        result = matcher.find_match(query, sample_embeddings)
        
        assert len(result.all_matches) == 3
        # Should be sorted by confidence (descending)
        confidences = [m["confidence"] for m in result.all_matches]
        assert confidences == sorted(confidences, reverse=True)
    
    def test_empty_database_returns_no_match(self, matcher):
        """Should handle empty enrollment database gracefully."""
        query = np.random.rand(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        result = matcher.find_match(query, {})
        
        assert result.matched is False
        assert result.inmate_id is None
        assert result.confidence == 0.0
        assert len(result.all_matches) == 0
    
    def test_single_enrollment_match(self, matcher):
        """Should work correctly with single enrolled embedding."""
        query = np.random.rand(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Very similar embedding
        enrolled = query + np.random.rand(512).astype(np.float32) * 0.01
        enrolled = enrolled / np.linalg.norm(enrolled)
        
        enrolled_db = {"inmate_001": enrolled}
        result = matcher.find_match(query, enrolled_db)
        
        assert len(result.all_matches) == 1
        assert result.all_matches[0]["inmate_id"] == "inmate_001"


class TestFaceMatcherRealEmbeddings:
    """Test matching with real LFW embeddings."""
    
    @pytest.fixture
    def embedder(self):
        return FaceEmbedder(model="Facenet512")
    
    @pytest.fixture
    def matcher(self):
        return FaceMatcher(threshold=0.75)
    
    def test_same_person_high_similarity(self, embedder, matcher):
        """Should produce high similarity for same person, different photos."""
        enroll_img = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        verify_img = SINGLE_ENROLLMENT / "lucy_liu_verify.jpg"
        
        emb_enroll = embedder.extract(enroll_img)
        emb_verify = embedder.extract(verify_img)
        
        similarity = matcher.calculate_similarity(emb_enroll, emb_verify)
        
        assert similarity > 0.6, f"Same person similarity too low: {similarity}"
    
    def test_different_people_low_similarity(self, embedder, matcher):
        """Should produce low similarity for different people."""
        person1 = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        person2 = SINGLE_ENROLLMENT / "michelle_rodriguez_enroll.jpg"
        
        emb1 = embedder.extract(person1)
        emb2 = embedder.extract(person2)
        
        similarity = matcher.calculate_similarity(emb1, emb2)
        
        assert similarity < 0.5, f"Different people similarity too high: {similarity}"
    
    def test_one_to_n_matching_with_real_embeddings(self, embedder, matcher):
        """Should correctly identify person in 1:N matching scenario."""
        # Build enrollment database
        enrolled_db = {
            "lucy": embedder.extract(SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"),
            "michelle": embedder.extract(SINGLE_ENROLLMENT / "michelle_rodriguez_enroll.jpg"),
            "vanessa": embedder.extract(SINGLE_ENROLLMENT / "vanessa_williams_enroll.jpg"),
        }
        
        # Query with Lucy's verification photo
        query = embedder.extract(SINGLE_ENROLLMENT / "lucy_liu_verify.jpg")
        
        result = matcher.find_match(query, enrolled_db)
        
        assert result.matched is True
        assert result.inmate_id == "lucy"
        assert result.confidence > 0.6


class TestFaceMatcherPerformance:
    """Test matching performance at different scales."""
    
    @pytest.fixture
    def matcher(self):
        return FaceMatcher(threshold=0.75)
    
    def test_matching_100_embeddings_performance(self, matcher):
        """Should match against 100 embeddings in <20ms."""
        import time
        
        # Create 100 enrolled embeddings
        enrolled_db = {}
        for i in range(100):
            emb = np.random.rand(512).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            enrolled_db[f"inmate_{i:03d}"] = emb
        
        # Query embedding
        query = np.random.rand(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Time the matching
        start = time.perf_counter()
        result = matcher.find_match(query, enrolled_db)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert result is not None
        assert elapsed < 20, f"Matching 100 embeddings took {elapsed:.2f}ms (should be <20ms)"
    
    def test_matching_1000_embeddings_performance(self, matcher):
        """Should match against 1000 embeddings in <50ms."""
        import time
        
        # Create 1000 enrolled embeddings
        enrolled_db = {}
        for i in range(1000):
            emb = np.random.rand(512).astype(np.float32)
            emb = emb / np.linalg.norm(emb)
            enrolled_db[f"inmate_{i:04d}"] = emb
        
        # Query embedding
        query = np.random.rand(512).astype(np.float32)
        query = query / np.linalg.norm(query)
        
        # Time the matching
        start = time.perf_counter()
        result = matcher.find_match(query, enrolled_db)
        elapsed = (time.perf_counter() - start) * 1000  # Convert to ms
        
        assert result is not None
        assert elapsed < 50, f"Matching 1000 embeddings took {elapsed:.2f}ms (should be <50ms)"
