"""
Integration tests for Sync API endpoints.

Tests queue synchronization endpoint with full request/response cycle.
"""
import base64
from datetime import datetime, timedelta
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """Create a test client with in-memory database."""
    return TestClient(app)


@pytest.fixture
def sample_image_base64():
    """Generate a sample base64 encoded image."""
    # Create a simple 1x1 pixel PNG
    img_bytes = base64.b64encode(b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde')
    return img_bytes.decode('utf-8')


@pytest.fixture
def sample_rollcall(client):
    """Create a sample roll call for testing."""
    scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
    payload = {
        "name": "Sync Test Roll Call",
        "scheduled_at": scheduled_at,
        "route": [
            {
                "id": "stop1",
                "location_id": "loc1",
                "order": 1,
                "expected_inmates": ["inmate1"],
                "status": "pending",
            }
        ],
        "officer_id": "officer1",
    }
    response = client.post("/api/v1/rollcalls", json=payload)
    return response.json()


class TestSyncQueueEndpoint:
    """Test POST /sync/queue endpoint."""

    def test_sync_empty_queue(self, client, sample_rollcall):
        """Should handle empty queue."""
        payload = {
            "roll_call_id": sample_rollcall["id"],
            "items": []
        }

        response = client.post("/api/v1/sync/queue", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 0
        assert data["results"] == []

    def test_sync_single_item(self, client, sample_rollcall, sample_image_base64):
        """Should process single queued item."""
        payload = {
            "roll_call_id": sample_rollcall["id"],
            "items": [
                {
                    "local_id": "queue001",
                    "queued_at": datetime.now().isoformat(),
                    "location_id": "loc1",
                    "image_data": sample_image_base64
                }
            ]
        }

        response = client.post("/api/v1/sync/queue", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 1
        assert len(data["results"]) == 1
        assert data["results"][0]["local_id"] == "queue001"

    def test_sync_multiple_items(self, client, sample_rollcall, sample_image_base64):
        """Should process multiple queued items in batch."""
        payload = {
            "roll_call_id": sample_rollcall["id"],
            "items": [
                {
                    "local_id": "queue001",
                    "queued_at": datetime.now().isoformat(),
                    "location_id": "loc1",
                    "image_data": sample_image_base64
                },
                {
                    "local_id": "queue002",
                    "queued_at": datetime.now().isoformat(),
                    "location_id": "loc1",
                    "image_data": sample_image_base64
                }
            ]
        }

        response = client.post("/api/v1/sync/queue", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 2
        assert len(data["results"]) == 2

    def test_sync_with_invalid_base64(self, client, sample_rollcall):
        """Should handle invalid base64 gracefully."""
        payload = {
            "roll_call_id": sample_rollcall["id"],
            "items": [
                {
                    "local_id": "queue001",
                    "queued_at": datetime.now().isoformat(),
                    "location_id": "loc1",
                    "image_data": "not-valid-base64!!!"
                }
            ]
        }

        response = client.post("/api/v1/sync/queue", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 1
        assert data["results"][0]["success"] is False
        assert data["results"][0]["error"] is not None

    def test_sync_partial_success(self, client, sample_rollcall, sample_image_base64):
        """Should handle partial success with mixed valid/invalid items."""
        payload = {
            "roll_call_id": sample_rollcall["id"],
            "items": [
                {
                    "local_id": "queue001",
                    "queued_at": datetime.now().isoformat(),
                    "location_id": "loc1",
                    "image_data": sample_image_base64
                },
                {
                    "local_id": "queue002",
                    "queued_at": datetime.now().isoformat(),
                    "location_id": "loc1",
                    "image_data": "invalid"
                }
            ]
        }

        response = client.post("/api/v1/sync/queue", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["processed"] == 2
        # First should succeed, second should fail
        assert data["results"][0]["success"] is True
        assert data["results"][1]["success"] is False

    def test_sync_with_nonexistent_rollcall(self, client, sample_image_base64):
        """Should handle non-existent roll call ID."""
        payload = {
            "roll_call_id": "nonexistent-id",
            "items": [
                {
                    "local_id": "queue001",
                    "queued_at": datetime.now().isoformat(),
                    "location_id": "loc1",
                    "image_data": sample_image_base64
                }
            ]
        }

        response = client.post("/api/v1/sync/queue", json=payload)

        # Could be 200 with errors in results, or 404
        # Depends on implementation choice
        assert response.status_code in [200, 404]

    def test_sync_missing_required_fields(self, client):
        """Should return 422 when required fields missing."""
        payload = {
            "items": []  # Missing roll_call_id
        }

        response = client.post("/api/v1/sync/queue", json=payload)

        assert response.status_code == 422  # Validation error