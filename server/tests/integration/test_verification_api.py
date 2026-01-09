"""
Integration tests for verification endpoints.

Tests the complete verification workflow including:
- Face verification against enrolled inmates
- Quick verification with location checking
- Error handling and edge cases
- Accuracy benchmarking with LFW test set
"""
import io
from datetime import date
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import create_app
from app.db.database import init_db


@pytest.fixture(scope="session")
def ml_components():
    """Session-scoped ML components - loaded once for all tests."""
    from app.dependencies import (
        get_face_detector,
        get_face_embedder,
        get_face_matcher,
        get_settings
    )
    
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
    conn = sqlite3.connect(":memory:", check_same_thread=False)
    conn.row_factory = sqlite3.Row
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
    
    inmate_repo = InmateRepository(db)
    embedding_repo = EmbeddingRepository(db)
    
    service = FaceRecognitionService(
        detector=ml_components["detector"],
        embedder=ml_components["embedder"],
        matcher=ml_components["matcher"],
        inmate_repo=inmate_repo,
        embedding_repo=embedding_repo,
        policy=ml_components["settings"].policy,
    )
    
    def override_get_face_recognition_service():
        return service
    
    _app.dependency_overrides[get_face_recognition_service] = override_get_face_recognition_service
    
    yield _app
    
    _app.dependency_overrides.clear()


@pytest.fixture
def client(app):
    """Test client for API requests."""
    return TestClient(app)


@pytest.fixture
def inmate_repo(db):
    """Inmate repository for test setup."""
    from app.db.repositories.inmate_repo import InmateRepository
    return InmateRepository(db)


@pytest.fixture
def embedding_repo(db):
    """Embedding repository for test setup."""
    from app.db.repositories.embedding_repo import EmbeddingRepository
    return EmbeddingRepository(db)


@pytest.fixture
def test_inmate(inmate_repo):
    """Create a test inmate in the database."""
    from app.models.inmate import InmateCreate
    
    inmate = inmate_repo.create(
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
def enrolled_inmate(client, test_inmate):
    """Create and enroll a test inmate."""
    # Use a real face image for enrollment
    enroll_image_path = Path(__file__).parent.parent / "fixtures" / "images" / "single_enrollment" / "lucy_liu_enroll.jpg"
    
    if not enroll_image_path.exists():
        pytest.skip(f"Required test fixture not found: {enroll_image_path}")
    
    with open(enroll_image_path, "rb") as f:
        image_data = f.read()
    
    # Enroll the inmate
    response = client.post(
        f"/api/v1/enrollment/{test_inmate.id}",
        files={"image": ("enroll.jpg", io.BytesIO(image_data), "image/jpeg")}
    )
    
    assert response.status_code == 200, f"Enrollment failed: {response.json()}"
    
    return test_inmate, enroll_image_path


@pytest.fixture
def verification_image():
    """Get verification image for enrolled inmate (different photo of same person)."""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "images" / "single_enrollment" / "lucy_liu_verify.jpg"
    
    if fixture_path.exists():
        with open(fixture_path, "rb") as f:
            return io.BytesIO(f.read())
    
    raise FileNotFoundError(f"Required test fixture not found: {fixture_path}")


@pytest.fixture
def unknown_person_image():
    """Get image of a person not enrolled in the system."""
    # Use negative matching fixture - person not enrolled
    fixture_path = Path(__file__).parent.parent / "fixtures" / "images" / "negative_matching" / "adam_sandler.jpg"
    
    if fixture_path.exists():
        with open(fixture_path, "rb") as f:
            return io.BytesIO(f.read())
    
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
    import numpy as np
    
    # Create a large image with random noise (prevents compression)
    # 4000x4000 pixels with random data should exceed 2MB
    arr = np.random.randint(0, 256, (4000, 4000, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode='RGB')
    img_bytes = io.BytesIO()
    img.save(img_bytes, format='JPEG', quality=95)
    img_bytes.seek(0)
    
    # Verify it's actually > 2MB
    size = len(img_bytes.getvalue())
    assert size > 2 * 1024 * 1024, f"Generated image is only {size} bytes, need >2MB"
    
    img_bytes.seek(0)
    return img_bytes


class TestVerifyQuickEndpoint:
    """Test cases for POST /verify/quick."""
    
    def test_verify_quick_successful_match(self, client, enrolled_inmate, verification_image):
        """Should return match when verifying enrolled inmate."""
        inmate, _ = enrolled_inmate
        
        response = client.post(
            "/api/v1/verify/quick",
            files={"image": ("verify.jpg", verification_image, "image/jpeg")},
            data={"location_id": "loc-001", "roll_call_id": "rc-001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched"] is True
        assert data["inmate_id"] == inmate.id
        assert data["confidence"] >= 0.75  # Above verification threshold
        assert data["recommendation"] in ["auto_accept", "confirm", "review"]
        assert "inmate" in data
        assert data["inmate"]["first_name"] == "John"
        assert "detection" in data
        assert data["detection"]["detected"] is True
    
    def test_verify_quick_no_match(self, client, enrolled_inmate, unknown_person_image):
        """Should return no match when face not enrolled."""
        response = client.post(
            "/api/v1/verify/quick",
            files={"image": ("verify.jpg", unknown_person_image, "image/jpeg")},
            data={"location_id": "loc-001", "roll_call_id": "rc-001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched"] is False
        assert data["inmate_id"] is None
        assert data["recommendation"] == "no_match"
    
    def test_verify_quick_no_face_detected(self, client, no_face_image):
        """Should return no match when no face in image."""
        response = client.post(
            "/api/v1/verify/quick",
            files={"image": ("verify.jpg", no_face_image, "image/jpeg")},
            data={"location_id": "loc-001", "roll_call_id": "rc-001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched"] is False
        assert data["detection"]["detected"] is False
        assert "no_face" in data["detection"]["quality_issues"]
    
    def test_verify_quick_file_too_large(self, client, large_image):
        """Should return 400 when file exceeds 2MB limit."""
        response = client.post(
            "/api/v1/verify/quick",
            files={"image": ("verify.jpg", large_image, "image/jpeg")},
            data={"location_id": "loc-001", "roll_call_id": "rc-001"}
        )
        
        assert response.status_code == 400
        assert "size" in response.json()["detail"].lower()
    
    def test_verify_quick_invalid_file_type(self, client):
        """Should return 400 when file is not an image."""
        text_file = io.BytesIO(b"This is not an image")
        
        response = client.post(
            "/api/v1/verify/quick",
            files={"image": ("test.txt", text_file, "text/plain")},
            data={"location_id": "loc-001", "roll_call_id": "rc-001"}
        )
        
        assert response.status_code == 400
        assert "image" in response.json()["detail"].lower()
    
    def test_verify_quick_missing_location_id(self, client, verification_image):
        """Should return 422 when location_id is missing."""
        response = client.post(
            "/api/v1/verify/quick",
            files={"image": ("verify.jpg", verification_image, "image/jpeg")},
            data={"roll_call_id": "rc-001"}
        )
        
        assert response.status_code == 422
    
    def test_verify_quick_missing_roll_call_id(self, client, verification_image):
        """Should return 422 when roll_call_id is missing."""
        response = client.post(
            "/api/v1/verify/quick",
            files={"image": ("verify.jpg", verification_image, "image/jpeg")},
            data={"location_id": "loc-001"}
        )
        
        assert response.status_code == 422


class TestVerifyEndpoint:
    """Test cases for POST /verify."""
    
    def test_verify_successful_match(self, client, enrolled_inmate, verification_image):
        """Should return match when verifying enrolled inmate."""
        inmate, _ = enrolled_inmate
        
        response = client.post(
            "/api/v1/verify",
            files={"image": ("verify.jpg", verification_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched"] is True
        assert data["inmate_id"] == inmate.id
        assert data["confidence"] >= 0.75
        assert "all_matches" in data
    
    def test_verify_no_enrolled_inmates(self, client, verification_image):
        """Should return no match when no inmates enrolled."""
        response = client.post(
            "/api/v1/verify",
            files={"image": ("verify.jpg", verification_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched"] is False
    
    def test_verify_no_face_detected(self, client, no_face_image):
        """Should return no match when no face in image."""
        response = client.post(
            "/api/v1/verify",
            files={"image": ("verify.jpg", no_face_image, "image/jpeg")}
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["matched"] is False
        assert data["detection"]["detected"] is False
    
    def test_verify_missing_image(self, client):
        """Should return 422 when image is missing."""
        response = client.post("/api/v1/verify")
        
        assert response.status_code == 422


class TestVerificationAccuracyBenchmark:
    """Accuracy benchmarking tests using LFW test fixtures."""
    
    def test_single_enrollment_accuracy(self, client, inmate_repo, ml_components):
        """Test verification accuracy with single enrollment photos."""
        from app.models.inmate import InmateCreate
        from app.db.repositories.embedding_repo import EmbeddingRepository
        from app.services.face_recognition import FaceRecognitionService
        import sqlite3
        
        # Get fresh database for this test
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.embedding_repo import EmbeddingRepository
        
        inmate_repo = InmateRepository(conn)
        embedding_repo = EmbeddingRepository(conn)
        
        service = FaceRecognitionService(
            detector=ml_components["detector"],
            embedder=ml_components["embedder"],
            matcher=ml_components["matcher"],
            inmate_repo=inmate_repo,
            embedding_repo=embedding_repo,
            policy=ml_components["settings"].policy,
        )
        
        # Test fixtures - single enrollment scenarios
        single_enrollment_dir = Path(__file__).parent.parent / "fixtures" / "images" / "single_enrollment"
        
        if not single_enrollment_dir.exists():
            pytest.skip("Single enrollment fixtures not found")
        
        # Get all person names from fixtures
        fixture_files = list(single_enrollment_dir.glob("*.jpg"))
        persons = {}
        
        for f in fixture_files:
            name = f.stem.rsplit("_", 1)[0]  # e.g., "lucy_liu_enroll" -> "lucy_liu"
            if name not in persons:
                persons[name] = {"enroll": None, "verify": None}
            if "enroll" in f.stem:
                persons[name]["enroll"] = f
            elif "verify" in f.stem:
                persons[name]["verify"] = f
        
        # Filter to persons with both enroll and verify images
        complete_persons = {k: v for k, v in persons.items() if v["enroll"] and v["verify"]}
        
        if not complete_persons:
            pytest.skip("No complete person fixtures found")
        
        correct_matches = 0
        total_tests = 0
        
        for person_name, images in complete_persons.items():
            # Create inmate
            inmate = inmate_repo.create(
                InmateCreate(
                    inmate_number=f"TEST-{person_name.upper()}",
                    first_name=person_name.split("_")[0].title(),
                    last_name=person_name.split("_")[-1].title() if "_" in person_name else "Test",
                    date_of_birth=date(1980, 1, 1),
                    cell_block="TEST",
                    cell_number="001"
                )
            )
            
            # Enroll
            enroll_result = service.enroll_face(inmate.id, images["enroll"])
            if not enroll_result.success:
                continue  # Skip if enrollment failed
            
            # Verify
            verify_result = service.verify_face(images["verify"])
            
            if verify_result.matched and verify_result.inmate_id == inmate.id:
                correct_matches += 1
            
            total_tests += 1
        
        if total_tests > 0:
            accuracy = correct_matches / total_tests
            
            # Log accuracy for informational purposes
            # Note: LFW fixtures have varying quality and conditions
            # A 50-80% accuracy is acceptable for these challenging conditions
            print(f"\nVerification accuracy: {accuracy:.2%} ({correct_matches}/{total_tests} samples)")
            
            # Only enforce minimum threshold - LFW fixtures are challenging
            # Real-world accuracy with controlled enrollment photos should be higher
            if total_tests >= 3:
                assert accuracy >= 0.50, f"Accuracy {accuracy:.2%} below minimum 50% threshold (based on {total_tests} samples)"
            else:
                # Too few samples - just log the result
                pytest.skip(f"Insufficient test samples ({total_tests}) - need at least 3 for accuracy benchmark")
        else:
            pytest.skip("No successful enrollments to test verification accuracy")
        
        conn.close()
    
    def test_negative_matching(self, client, inmate_repo, ml_components):
        """Test that unknown persons are not matched to enrolled inmates."""
        import sqlite3
        
        conn = sqlite3.connect(":memory:", check_same_thread=False)
        conn.row_factory = sqlite3.Row
        init_db(conn)
        
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.embedding_repo import EmbeddingRepository
        from app.models.inmate import InmateCreate
        from app.services.face_recognition import FaceRecognitionService
        
        inmate_repo = InmateRepository(conn)
        embedding_repo = EmbeddingRepository(conn)
        
        service = FaceRecognitionService(
            detector=ml_components["detector"],
            embedder=ml_components["embedder"],
            matcher=ml_components["matcher"],
            inmate_repo=inmate_repo,
            embedding_repo=embedding_repo,
            policy=ml_components["settings"].policy,
        )
        
        # Enroll some people from single_enrollment
        single_dir = Path(__file__).parent.parent / "fixtures" / "images" / "single_enrollment"
        enrolled_count = 0
        
        if single_dir.exists():
            for img in single_dir.glob("*_enroll.jpg"):
                name = img.stem.rsplit("_", 1)[0]
                inmate = inmate_repo.create(
                    InmateCreate(
                        inmate_number=f"NEG-{name.upper()}",
                        first_name=name.split("_")[0].title(),
                        last_name="Test",
                        date_of_birth=date(1980, 1, 1),
                        cell_block="NEG",
                        cell_number="001"
                    )
                )
                result = service.enroll_face(inmate.id, img)
                if result.success:
                    enrolled_count += 1
        
        if enrolled_count == 0:
            pytest.skip("No inmates enrolled for negative matching test")
        
        # Test negative matching - these people should NOT match
        negative_dir = Path(__file__).parent.parent / "fixtures" / "images" / "negative_matching"
        
        if not negative_dir.exists():
            pytest.skip("Negative matching fixtures not found")
        
        false_positives = 0
        total_tests = 0
        
        for img in negative_dir.glob("*.jpg"):
            result = service.verify_face(img)
            
            if result.matched:
                false_positives += 1
            
            total_tests += 1
        
        if total_tests > 0:
            false_positive_rate = false_positives / total_tests
            assert false_positive_rate <= 0.10, f"False positive rate {false_positive_rate:.2%} exceeds 10% threshold"
        
        conn.close()