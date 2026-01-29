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

    def test_list_rollcalls_includes_statistics(self, client, sample_route):
        """Should include verification statistics in roll call list."""
        # Create a roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        payload = {
            "name": "Stats Test Roll Call",
            "scheduled_at": scheduled_at,
            "route": sample_route,
            "officer_id": "officer1",
        }
        create_response = client.post("/api/v1/rollcalls", json=payload)
        rollcall_id = create_response.json()["id"]

        # List roll calls
        response = client.get("/api/v1/rollcalls")

        assert response.status_code == 200
        data = response.json()

        # Find our roll call in the list
        our_rollcall = next((rc for rc in data if rc["id"] == rollcall_id), None)
        assert our_rollcall is not None

        # Verify statistics are present
        assert "total_stops" in our_rollcall
        assert "expected_inmates" in our_rollcall
        assert "verified_inmates" in our_rollcall
        assert "progress_percentage" in our_rollcall

        # Verify values match the test data
        assert our_rollcall["total_stops"] == 2
        assert our_rollcall["expected_inmates"] == 3  # 2 + 1 from sample_route
        assert our_rollcall["verified_inmates"] == 0  # No verifications yet
        assert our_rollcall["progress_percentage"] == 0.0

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


class TestGenerateRollCallEndpoint:
    """Test roll call generation endpoint."""

    def test_generate_rollcall_success(self, client):
        """Should generate roll call for a location."""
        # Create location hierarchy
        houseblock_payload = {
            "name": "Houseblock 1",
            "type": "houseblock",
            "building": "Block 1",
        }
        hb_response = client.post("/api/v1/locations", json=houseblock_payload)
        houseblock_id = hb_response.json()["id"]
        
        wing_payload = {
            "name": "A Wing",
            "type": "wing",
            "building": "Block 1",
            "parent_id": houseblock_id,
        }
        wing_response = client.post("/api/v1/locations", json=wing_payload)
        wing_id = wing_response.json()["id"]
        
        cell_payload = {
            "name": "A1-01",
            "type": "cell",
            "building": "Block 1",
            "parent_id": wing_id,
        }
        client.post("/api/v1/locations", json=cell_payload)
        
        # Generate roll call
        generate_payload = {
            "location_id": houseblock_id,
            "scheduled_at": "2026-01-29T14:00:00",
        }
        response = client.post("/api/v1/rollcalls/generate", json=generate_payload)
        
        assert response.status_code == 200
        data = response.json()
        assert data["location_id"] == houseblock_id
        assert data["location_name"] == "Houseblock 1"
        assert "route" in data
        assert "summary" in data
        assert data["summary"]["total_locations"] >= 1

    def test_generate_rollcall_not_found(self, client):
        """Should return 404 for non-existent location."""
        generate_payload = {
            "location_id": "non-existent-id",
            "scheduled_at": "2026-01-29T14:00:00",
        }
        response = client.post("/api/v1/rollcalls/generate", json=generate_payload)
        
        assert response.status_code == 404

    def test_generate_rollcall_includes_empty_by_default(self, client):
        """Should include empty cells by default."""
        # Create location hierarchy
        houseblock_payload = {
            "name": "Houseblock 2",
            "type": "houseblock",
            "building": "Block 2",
        }
        hb_response = client.post("/api/v1/locations", json=houseblock_payload)
        houseblock_id = hb_response.json()["id"]
        
        # Create 2 cells
        for i in range(2):
            cell_payload = {
                "name": f"B1-{i+1:02d}",
                "type": "cell",
                "building": "Block 2",
                "parent_id": houseblock_id,
            }
            client.post("/api/v1/locations", json=cell_payload)
        
        generate_payload = {
            "location_id": houseblock_id,
            "scheduled_at": "2026-01-29T14:00:00",
        }
        response = client.post("/api/v1/rollcalls/generate", json=generate_payload)
        
        data = response.json()
        # All cells should be in route even though empty
        assert len(data["route"]) == 2
        assert data["summary"]["empty_locations"] == 2


class TestExpectedPrisonersEndpoint:
    """Test expected prisoners endpoint."""

    def test_get_expected_prisoners_empty_cell(self, client):
        """Should return empty list for cell with no inmates."""
        cell_payload = {
            "name": "Empty Cell",
            "type": "cell",
            "building": "Block 1",
        }
        cell_response = client.post("/api/v1/locations", json=cell_payload)
        cell_id = cell_response.json()["id"]
        
        response = client.get(f"/api/v1/rollcalls/expected/{cell_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["location_id"] == cell_id
        assert data["expected_prisoners"] == []
        assert data["total_expected"] == 0

    def test_get_expected_prisoners_with_inmate(self, client):
        """Should return prisoners assigned to cell."""
        # Create cell
        cell_payload = {
            "name": "Occupied Cell",
            "type": "cell",
            "building": "Block 1",
        }
        cell_response = client.post("/api/v1/locations", json=cell_payload)
        cell_id = cell_response.json()["id"]
        
        # Create inmate
        inmate_payload = {
            "inmate_number": "Z001",
            "first_name": "Test",
            "last_name": "Prisoner",
            "date_of_birth": "1985-06-15",
            "cell_block": "Z",
            "cell_number": "001",
        }
        inmate_response = client.post("/api/v1/inmates", json=inmate_payload)
        inmate_id = inmate_response.json()["id"]
        
        # Assign to cell via update
        client.put(f"/api/v1/inmates/{inmate_id}", json={
            "home_cell_id": cell_id,
        })
        
        response = client.get(f"/api/v1/rollcalls/expected/{cell_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["total_expected"] == 1
        assert data["expected_prisoners"][0]["inmate_id"] == inmate_id


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
