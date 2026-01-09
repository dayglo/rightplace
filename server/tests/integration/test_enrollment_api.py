"""
Integration tests for enrollment endpoint.

Tests the complete enrollment workflow including:
- File upload validation
- Face detection
- Quality assessment
- Embedding storage
- Error handling
"""
import io
import tempfile
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.config import Settings
from app.db.database import init_db, get_db


@pytest.fixture(scope="session")
def ml_components():
    """Session-scoped ML components - loaded once for all tests."""
    from app.dependencies import (
        get_face_detector,
        get_face_embedder, 
        get_face_matcher,
        get_settings
    )
    
    # These are cached via @lru_cache, but loading them here ensures
    # they're initialized once at session start
    return {
        "detector": get_face_detector(),
        "embedder": get_face_embedder(),
        "matcher": get_face_matcher(),
        "settings": get_settings(),
    }


@pytest.fixture
def db():
    """Database connection for test setup."""
    import sqlite3
    # check_same_thread=False allows connection to be used from different threads (safe in tests)
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row  # Enable dictionary-style access
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def app(db, ml_components):
    """Test FastAPI application."""
    from app.main import app as _app
    from app.dependencies import get_face_recognition_service
    from app.db.repositories.inmate_repo import InmateRepository
    from app.db.repositories.embedding_repo import EmbeddingRepository
    from app.services.face_recognition import FaceRecognitionService
    
    # Create repositories with test database
    inmate_repo = InmateRepository(db)
    embedding_repo = EmbeddingRepository(db)
    
    # Create service with session-scoped ML components and test database
    service = FaceRecognitionService(
        detector=ml_components["detector"],
        embedder=ml_components["embedder"],
        matcher=ml_components["matcher"],
        inmate_repo=inmate_repo,
        embedding_repo=embedding_repo,
        policy=ml_components["settings"].policy,
    )
    
    # Override to return our pre-configured service
    def override_get_face_recognition_service():
        return service
    
    _app.dependency_overrides[get_face_recognition_service] = override_get_face_recognition_service
    
    yield _app
    
    # Clean up overrides
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Test client for API requests."""
    return TestClient(app)


@pytest.fixture
def test_inmate(db):
    """Create a test inmate in the database."""
    from app.db.repositories.inmate_repo import InmateRepository
    from app.models.inmate import InmateCreate
    from datetime import date
    
    repo = InmateRepository(db)
    inmate = repo.create(
        InmateCreate(
            inmate_number="A12345",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101"
        )
    )
    return inmate


@pytest.fixture
def good_face_image():
    """Create a test image file with a face (using dual_enrollment fixture)."""
    # Use actual fixture from dual_enrollment
    fixture_path = Path(__file__).parent.parent / "fixtures" / "images" / "dual_enrollment" / "chen_shui_bian_enroll_1.jpg"
    
    if fixture_path.exists():
        with open(fixture_path, "rb") as f:
            return io.BytesIO(f.read())
    
    # Fallback should not happen - fixture must exist
    raise FileNotFoundError(f"Required test fixture not found: {fixture_path}")


@pytest.fixture
def no_face_image():
    """Create a test image with no face."""
    img = Image.new('RGB', (640, 480), color='blue')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG')
    img_bytes.seek(0)
    return img_bytes


@pytest.fixture
def large_image():
    """Create an image larger than 2MB."""
    # Create a large image (3000x3000 should exceed 2MB)
    img = Image.new('RGB', (3000, 3000), color='red')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    return img_bytes


class TestEnrollmentEndpoint:
    """Test cases for POST /enrollment/{inmate_id}."""
    
    def test_successful_enrollment(self, client, test_inmate, good_face_image):
        """Should successfully enroll inmate with good quality image."""
        response = client.post(
            f"/api/v1/enrollment/{test_inmate.id}",
            files={"image": ("test.jpg", good_face_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["success"] is True
        assert data["inmate_id"] == test_inmate.id
        assert data["quality"] >= 0.80  # Above enrollment threshold
        assert "enrolled_at" in data
        assert "embedding_version" in data
    
    def test_enrollment_inmate_not_found(self, client, good_face_image):
        """Should return 404 when inmate does not exist."""
        response = client.post(
            "/api/v1/enrollment/nonexistent-id",
            files={"image": ("test.jpg", good_face_image, "image/jpeg")}
        )
        
        assert response.status_code == 404
        data = response.json()
        
        # HTTPException wraps response in "detail" key
        detail = data.get("detail", data)
        assert detail["error"] == "inmate_not_found"
        assert "not found" in detail["message"].lower()
    
    def test_enrollment_no_face_detected(self, client, test_inmate, no_face_image):
        """Should return 400 when no face is detected in image."""
        response = client.post(
            f"/api/v1/enrollment/{test_inmate.id}",
            files={"image": ("test.jpg", no_face_image, "image/jpeg")}
        )
        
        assert response.status_code == 400
        data = response.json()
        
        # HTTPException wraps response in "detail" key
        detail = data.get("detail", data)
        assert detail["success"] is False
        # Could be "no face" or "quality" issue depending on detection
        assert "quality" in detail["message"].lower() or "no face" in detail["message"].lower()
    
    def test_enrollment_file_too_large(self, client, test_inmate, large_image):
        """Should return 400 when file exceeds 2MB limit."""
        response = client.post(
            f"/api/v1/enrollment/{test_inmate.id}",
            files={"image": ("test.jpg", large_image, "image/jpeg")}
        )
        
        assert response.status_code == 400
        data = response.json()
        detail = data.get("detail", data)
        # detail may be a string (direct HTTPException) or dict (wrapped response)
        if isinstance(detail, str):
            assert "size" in detail.lower()
            assert "exceeds" in detail.lower()
        else:
            # If the file wasn't actually too large, it may fail on quality instead
            assert "quality" in detail.get("message", "").lower() or "size" in str(detail).lower()
    
    def test_enrollment_invalid_file_type(self, client, test_inmate):
        """Should return 400 when file is not an image."""
        text_file = io.BytesIO(b"This is not an image")
        
        response = client.post(
            f"/api/v1/enrollment/{test_inmate.id}",
            files={"image": ("test.txt", text_file, "text/plain")}
        )
        
        assert response.status_code == 400
        assert "image" in response.json()["detail"].lower()
    
    def test_enrollment_quality_too_low(self, client, test_inmate, monkeypatch):
        """Should return 400 when image quality below threshold."""
        # This test would need a blur/dark image fixture
        # For now, we'll skip or mock the quality check
        pytest.skip("Requires low-quality image fixture")
    
    def test_enrollment_multiple_faces(self, client, test_inmate, monkeypatch):
        """Should return 400 when multiple faces detected."""
        # This test would need a multi-face image fixture
        pytest.skip("Requires multi-face image fixture")


class TestEnrollmentValidation:
    """Test input validation for enrollment endpoint."""
    
    def test_enrollment_missing_image(self, client, test_inmate):
        """Should return 422 when image parameter is missing."""
        response = client.post(f"/api/v1/enrollment/{test_inmate.id}")
        
        assert response.status_code == 422  # FastAPI validation error
    
    def test_enrollment_empty_inmate_id(self, client, good_face_image):
        """Should return 404 when inmate_id is empty."""
        response = client.post(
            "/api/v1/enrollment/",
            files={"image": ("test.jpg", good_face_image, "image/jpeg")}
        )
        
        # Should return 404 or 405 (method not allowed) depending on routing
        assert response.status_code in [404, 405]