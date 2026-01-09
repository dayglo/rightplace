"""
Integration tests for Roll Call API endpoints.

Tests CRUD operations, status transitions, and workflow management.
"""
import pytest
from fastapi.testclient import TestClient
from datetime import datetime, timedelta

from app.main import app
from app.db.database import get_connection, init_db


@pytest.fixture
def client():
    """Create a test client with in-memory database."""
    return TestClient(app)


@pytest.fixture
def sample_route():
    """Sample route stops for testing."""
    return [
        {
            "id": "stop1",
            "location_id": "loc1",
            "order": 1,
            "expected_inmates": ["inmate1", "inmate2"],
            "status": "pending",
        },
        {
            "id": "stop2",
            "location_id": "loc2",
            "order": 2,
            "expected_inmates": ["inmate3"],
            "status": "pending",
        },
    ]


class TestRollCallsCRUD:
    """Test roll call CRUD endpoints."""

    def test_create_rollcall_success(self, client, sample_route):
        """Should create roll call with valid data."""
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        payload = {
            "name": "Morning Roll Call",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
            "notes": "Test roll call",
        }

        response = client.post("/api/v1/rollcalls", json=payload)

        assert response.status_code == 201
        data = response.json()
        assert data["name"] == "Morning Roll Call"
        assert data["status"] == "scheduled"
        assert "id" in data

    def test_create_rollcall_empty_route_fails(self, client):
        """Should return 400 when route is empty."""
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        
        payload = {
            "name": "Empty Route Roll Call",
            "scheduled_at": scheduled_at,
            "route": [],
            "officer_id": "officer1",
        }

        response = client.post("/api/v1/rollcalls", json=payload)

        assert response.status_code == 400
        assert "Route cannot be empty" in response.json()["detail"]

    def test_create_rollcall_past_time_fails(self, client, sample_route):
        """Should return 400 when scheduled time is in the past."""
        past_time = (datetime.now() - timedelta(hours=1)).isoformat()
        
        payload = {
            "name": "Past Roll Call",
            "scheduled_at": past_time,
            "route": sample_route,
            "officer_id": "officer1",
        }

        response = client.post("/api/v1/rollcalls", json=payload)

        assert response.status_code == 400
        assert "past" in response.json()["detail"].lower()

    def test_get_rollcall_by_id(self, client, sample_route):
        """Should retrieve roll call by ID."""
        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "Test Roll Call",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Get roll call
        response = client.get(f"/api/v1/rollcalls/{rollcall_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == rollcall_id
        assert data["name"] == "Test Roll Call"

    def test_get_rollcall_not_found(self, client):
        """Should return 404 for non-existent roll call."""
        response = client.get("/api/v1/rollcalls/non-existent-id")
        assert response.status_code == 404

    def test_list_rollcalls(self, client, sample_route):
        """Should list all roll calls."""
        # Create two roll calls
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        for i in range(2):
            payload = {
                "name": f"Roll Call {i}",
                "scheduled_at": scheduled_at,
                "route": sample_route,
                "officer_id": "officer1",
            }
            client.post("/api/v1/rollcalls", json=payload)

        # List roll calls
        response = client.get("/api/v1/rollcalls")

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 2

    def test_delete_rollcall(self, client, sample_route):
        """Should delete roll call."""
        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "To Delete",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Delete roll call
        response = client.delete(f"/api/v1/rollcalls/{rollcall_id}")

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/rollcalls/{rollcall_id}")
        assert get_response.status_code == 404


class TestRollCallStatusTransitions:
    """Test roll call status transition endpoints."""

    def test_start_rollcall(self, client, sample_route):
        """Should start a scheduled roll call."""
        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "To Start",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Start roll call
        response = client.post(f"/api/v1/rollcalls/{rollcall_id}/start")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"
        assert data["started_at"] is not None

    def test_start_rollcall_already_started(self, client, sample_route):
        """Should return 400 when starting already started roll call."""
        # Create and start roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "Already Started",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]
        client.post(f"/api/v1/rollcalls/{rollcall_id}/start")

        # Try to start again
        response = client.post(f"/api/v1/rollcalls/{rollcall_id}/start")

        assert response.status_code == 400
        assert "already" in response.json()["detail"].lower()

    def test_complete_rollcall(self, client, sample_route):
        """Should complete an in-progress roll call."""
        # Create and start roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "To Complete",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]
        client.post(f"/api/v1/rollcalls/{rollcall_id}/start")

        # Complete roll call
        response = client.post(f"/api/v1/rollcalls/{rollcall_id}/complete")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "completed"
        assert data["completed_at"] is not None

    def test_complete_rollcall_not_started(self, client, sample_route):
        """Should return 400 when completing non-started roll call."""
        # Create roll call (but don't start)
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "Not Started",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Try to complete
        response = client.post(f"/api/v1/rollcalls/{rollcall_id}/complete")

        assert response.status_code == 400
        assert "not in progress" in response.json()["detail"].lower()

    def test_cancel_rollcall(self, client, sample_route):
        """Should cancel a roll call with reason."""
        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "To Cancel",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Cancel roll call
        cancel_payload = {"reason": "Emergency situation"}
        response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/cancel", json=cancel_payload
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "cancelled"
        assert data["cancelled_reason"] == "Emergency situation"

    def test_cancel_rollcall_requires_reason(self, client, sample_route):
        """Should return 400 when cancel reason missing."""
        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "To Cancel",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Cancel without reason
        cancel_payload = {"reason": ""}
        response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/cancel", json=cancel_payload
        )

        assert response.status_code == 400


class TestVerificationRecording:
    """Test verification recording endpoint."""

    def test_record_verification(self, client, sample_route):
        """Should record verification for roll call."""
        # Create inmate first (required by foreign key constraint)
        inmate_payload = {
            "inmate_number": "A12345",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "cell_block": "A",
            "cell_number": "101",
        }
        inmate_response = client.post("/api/v1/inmates", json=inmate_payload)
        inmate_id = inmate_response.json()["id"]
        
        # Create location first (required by foreign key constraint)
        location_payload = {
            "name": "Cell Block A",
            "type": "block",
            "building": "Main",
        }
        location_response = client.post("/api/v1/locations", json=location_payload)
        location_id = location_response.json()["id"]
        
        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "Verification Test",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Record verification
        verification_payload = {
            "inmate_id": inmate_id,
            "location_id": location_id,
            "status": "verified",
            "confidence": 0.89,
            "is_manual_override": False,
        }
        response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/verification",
            json=verification_payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["roll_call_id"] == rollcall_id
        assert data["inmate_id"] == inmate_id
        assert data["status"] == "verified"
        assert data["confidence"] == 0.89

    def test_record_manual_override_verification(self, client, sample_route):
        """Should record manual override verification."""
        # Create inmate first (required by foreign key constraint)
        inmate_payload = {
            "inmate_number": "A12346",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1991-02-02",
            "cell_block": "B",
            "cell_number": "201",
        }
        inmate_response = client.post("/api/v1/inmates", json=inmate_payload)
        inmate_id = inmate_response.json()["id"]
        
        # Create location first (required by foreign key constraint)
        location_payload = {
            "name": "Cell Block B",
            "type": "block",
            "building": "Main",
        }
        location_response = client.post("/api/v1/locations", json=location_payload)
        location_id = location_response.json()["id"]
        
        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_payload = {
            "name": "Manual Override Test",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=create_payload)
        rollcall_id = create_response.json()["id"]

        # Record manual override
        verification_payload = {
            "inmate_id": inmate_id,
            "location_id": location_id,
            "status": "manual",
            "confidence": 0.0,
            "is_manual_override": True,
            "manual_override_reason": "facial_injury",
            "notes": "Inmate has bandage",
        }
        response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/verification",
            json=verification_payload,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["is_manual_override"] is True
        assert data["manual_override_reason"] == "facial_injury"
        assert data["notes"] == "Inmate has bandage"
