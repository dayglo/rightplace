"""
Unit tests for FaceEmbedder wrapper.

Tests the face embedding extraction functionality using LFW test fixtures.
"""

import numpy as np
import pytest
from pathlib import Path

from app.ml.face_embedder import FaceEmbedder


# Fixture paths
FIXTURES_DIR = Path(__file__).parent.parent / "fixtures" / "images"
SINGLE_ENROLLMENT = FIXTURES_DIR / "single_enrollment"
DUAL_ENROLLMENT = FIXTURES_DIR / "dual_enrollment"


class TestFaceEmbedder:
    """Test suite for FaceEmbedder class."""
    
    @pytest.fixture
    def embedder(self):
        """Create a FaceEmbedder instance with default model."""
        return FaceEmbedder(model="Facenet512")
    
    def test_extract_single_face_returns_embedding(self, embedder):
        """Should extract 512-dimensional embedding from image."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedding = embedder.extract(image_path)
        
        assert embedding is not None
        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (512,)
        assert embedding.dtype == np.float32 or embedding.dtype == np.float64
    
    def test_extract_same_image_produces_identical_embeddings(self, embedder):
        """Should produce identical embeddings for the same image."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedding1 = embedder.extract(image_path)
        embedding2 = embedder.extract(image_path)
        
        # Embeddings should be identical (or very close due to floating point)
        np.testing.assert_array_almost_equal(embedding1, embedding2, decimal=5)
    
    def test_embedding_is_normalized(self, embedder):
        """Should return L2-normalized embedding."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedding = embedder.extract(image_path)
        
        # L2 norm should be approximately 1.0
        norm = np.linalg.norm(embedding)
        assert abs(norm - 1.0) < 0.1, f"Embedding not normalized: norm={norm}"
    
    def test_same_person_different_photos_high_similarity(self, embedder):
        """Should produce similar embeddings for different photos of same person."""
        enroll_img = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        verify_img = SINGLE_ENROLLMENT / "lucy_liu_verify.jpg"
        
        embedding1 = embedder.extract(enroll_img)
        embedding2 = embedder.extract(verify_img)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        
        # Same person should have high similarity (>0.6)
        assert similarity > 0.6, f"Same person similarity too low: {similarity}"
    
    def test_different_people_low_similarity(self, embedder):
        """Should produce dissimilar embeddings for different people."""
        person1 = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        person2 = SINGLE_ENROLLMENT / "michelle_rodriguez_enroll.jpg"
        
        embedding1 = embedder.extract(person1)
        embedding2 = embedder.extract(person2)
        
        # Calculate cosine similarity
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        
        # Different people should have lower similarity (<0.5)
        assert similarity < 0.5, f"Different people similarity too high: {similarity}"
    
    def test_extract_diverse_subjects(self, embedder):
        """Should extract embeddings across diverse subjects."""
        test_images = [
            "lucy_liu_enroll.jpg",  # Asian Female
            "michelle_rodriguez_enroll.jpg",  # Hispanic Female
            "vanessa_williams_enroll.jpg",  # African American Female
            "harbhajan_singh_enroll.jpg",  # South Asian Male
            "sergio_garcia_enroll.jpg",  # Hispanic Male
        ]
        
        for image_name in test_images:
            image_path = SINGLE_ENROLLMENT / image_name
            embedding = embedder.extract(image_path)
            
            assert embedding is not None, f"Failed to extract embedding from {image_name}"
            assert embedding.shape == (512,), f"Wrong shape for {image_name}"
            assert np.any(embedding != 0), f"Zero embedding for {image_name}"
    
    def test_extract_nonexistent_image_raises_error(self, embedder):
        """Should raise appropriate error for nonexistent image."""
        with pytest.raises((FileNotFoundError, ValueError, Exception)):
            embedder.extract("nonexistent.jpg")
    
    def test_dual_enrollment_consistency(self, embedder):
        """Should produce consistent embeddings for dual enrollment photos."""
        person = "lucy_liu"
        
        # Get enrollment photos (if they exist in dual_enrollment)
        enroll1 = SINGLE_ENROLLMENT / f"{person}_enroll.jpg"
        verify1 = SINGLE_ENROLLMENT / f"{person}_verify.jpg"
        
        if enroll1.exists() and verify1.exists():
            embedding1 = embedder.extract(enroll1)
            embedding2 = embedder.extract(verify1)
            
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            
            assert similarity > 0.5, f"Enrollment consistency too low: {similarity}"


class TestFaceEmbedderModels:
    """Test model switching functionality."""
    
    def test_facenet512_model_works(self):
        """Should extract embeddings with Facenet512 model."""
        embedder = FaceEmbedder(model="Facenet512")
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedding = embedder.extract(image_path)
        
        assert embedding is not None
        assert embedding.shape == (512,)
    
    def test_arcface_model_works(self):
        """Should extract embeddings with ArcFace model."""
        embedder = FaceEmbedder(model="ArcFace")
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedding = embedder.extract(image_path)
        
        assert embedding is not None
        assert embedding.shape == (512,)
    
    def test_both_models_produce_512_dim_embeddings(self):
        """Should produce 512-dimensional embeddings with both models."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedder_facenet = FaceEmbedder(model="Facenet512")
        embedder_arcface = FaceEmbedder(model="ArcFace")
        
        embedding_facenet = embedder_facenet.extract(image_path)
        embedding_arcface = embedder_arcface.extract(image_path)
        
        assert embedding_facenet.shape == (512,)
        assert embedding_arcface.shape == (512,)
    
    def test_different_models_produce_different_embeddings(self):
        """Should produce different embeddings with different models."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedder_facenet = FaceEmbedder(model="Facenet512")
        embedder_arcface = FaceEmbedder(model="ArcFace")
        
        embedding_facenet = embedder_facenet.extract(image_path)
        embedding_arcface = embedder_arcface.extract(image_path)
        
        # Different models should produce different embeddings
        # (but both should be valid)
        are_different = not np.allclose(embedding_facenet, embedding_arcface, rtol=0.1)
        assert are_different, "Different models produced identical embeddings"


class TestFaceEmbedderConsistency:
    """Test embedding consistency and quality."""
    
    @pytest.fixture
    def embedder(self):
        return FaceEmbedder(model="Facenet512")
    
    def test_cross_gender_consistency(self, embedder):
        """Should produce consistent embeddings across genders."""
        male_images = [
            "harbhajan_singh_enroll.jpg",
            "sergio_garcia_enroll.jpg",
        ]
        
        female_images = [
            "lucy_liu_enroll.jpg",
            "michelle_rodriguez_enroll.jpg",
            "vanessa_williams_enroll.jpg",
        ]
        
        # Extract embeddings
        male_embeddings = [
            embedder.extract(SINGLE_ENROLLMENT / img) for img in male_images
        ]
        female_embeddings = [
            embedder.extract(SINGLE_ENROLLMENT / img) for img in female_images
        ]
        
        # All should be valid
        assert all(emb.shape == (512,) for emb in male_embeddings)
        assert all(emb.shape == (512,) for emb in female_embeddings)
        
        # All should have reasonable norms
        male_norms = [np.linalg.norm(emb) for emb in male_embeddings]
        female_norms = [np.linalg.norm(emb) for emb in female_embeddings]
        
        assert all(0.5 < norm < 1.5 for norm in male_norms)
        assert all(0.5 < norm < 1.5 for norm in female_norms)
    
    def test_embedding_values_in_reasonable_range(self, embedder):
        """Should produce embedding values in reasonable range."""
        image_path = SINGLE_ENROLLMENT / "lucy_liu_enroll.jpg"
        
        embedding = embedder.extract(image_path)
        
        # Values should be in a reasonable range (typically -1 to 1 for normalized)
        assert np.all(np.abs(embedding) <= 10), "Embedding values out of reasonable range"
        
        # Should not be all zeros
        assert np.any(embedding != 0), "Embedding is all zeros"
        
        # Should not be all the same value
        assert len(np.unique(embedding)) > 10, "Embedding lacks diversity in values"


class TestFaceEmbedderEdgeCases:
    """Test edge cases and error handling."""
    
    @pytest.fixture
    def embedder(self):
        return FaceEmbedder(model="Facenet512")
    
    def test_multiple_people_in_dual_enrollment(self, embedder):
        """Should handle multiple enrollment photos of same person."""
        # Use dual enrollment fixtures
        person = "chen_shui_bian"
        enroll1 = DUAL_ENROLLMENT / f"{person}_enroll_1.jpg"
        enroll2 = DUAL_ENROLLMENT / f"{person}_enroll_2.jpg"
        
        if enroll1.exists() and enroll2.exists():
            embedding1 = embedder.extract(enroll1)
            embedding2 = embedder.extract(enroll2)
            
            # Should produce similar embeddings
            similarity = np.dot(embedding1, embedding2) / (
                np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
            )
            
            assert similarity > 0.6, f"Dual enrollment similarity too low: {similarity}"
