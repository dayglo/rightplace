"""Integration tests for locations CRUD endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestLocationsCRUD:
    """Test suite for locations CRUD endpoints."""

    def test_create_location_returns_201(self, client: TestClient):
        """Should create a new location and return 201."""
        location_data = {
            "name": "Cell Block A",
            "type": "block",
            "building": "Main",
            "floor": 1,
            "capacity": 50
        }
        response = client.post("/api/v1/locations", json=location_data)
        assert response.status_code == 201

    def test_create_location_response_structure(self, client: TestClient):
        """Should return complete location object with generated ID."""
        location_data = {
            "name": "Cell Block B",
            "type": "block",
            "building": "Main",
            "floor": 2,
            "capacity": 50
        }
        response = client.post("/api/v1/locations", json=location_data)
        data = response.json()
        
        assert "id" in data
        assert data["name"] == "Cell Block B"
        assert data["type"] == "block"
        assert data["building"] == "Main"
        assert data["floor"] == 2
        assert data["capacity"] == 50

    def test_get_all_locations_returns_200(self, client: TestClient):
        """Should return list of all locations."""
        response = client.get("/api/v1/locations")
        assert response.status_code == 200

    def test_get_all_locations_returns_list(self, client: TestClient):
        """Should return a list (even if empty)."""
        response = client.get("/api/v1/locations")
        data = response.json()
        assert isinstance(data, list)

    def test_get_location_by_id_returns_200(self, client: TestClient):
        """Should return location when valid ID provided."""
        # First create a location
        location_data = {
            "name": "Medical Wing",
            "type": "medical",
            "building": "East",
            "floor": 1,
            "capacity": 20
        }
        create_response = client.post("/api/v1/locations", json=location_data)
        created_location = create_response.json()
        location_id = created_location["id"]
        
        # Then get it by ID
        response = client.get(f"/api/v1/locations/{location_id}")
        assert response.status_code == 200

    def test_get_location_by_id_not_found(self, client: TestClient):
        """Should return 404 when location doesn't exist."""
        response = client.get("/api/v1/locations/nonexistent-id")
        assert response.status_code == 404

    def test_update_location_returns_200(self, client: TestClient):
        """Should update location and return 200."""
        # Create a location
        location_data = {
            "name": "Yard A",
            "type": "yard",
            "building": "Outdoor",
            "floor": 0,
            "capacity": 100
        }
        create_response = client.post("/api/v1/locations", json=location_data)
        created_location = create_response.json()
        location_id = created_location["id"]
        
        # Update the location
        update_data = {
            "capacity": 150
        }
        response = client.put(f"/api/v1/locations/{location_id}", json=update_data)
        assert response.status_code == 200

    def test_update_location_changes_data(self, client: TestClient):
        """Should actually update the location data."""
        # Create a location
        location_data = {
            "name": "Admin Office",
            "type": "admin",
            "building": "Admin",
            "floor": 1,
            "capacity": 5
        }
        create_response = client.post("/api/v1/locations", json=location_data)
        created_location = create_response.json()
        location_id = created_location["id"]
        
        # Update the location
        update_data = {
            "capacity": 10
        }
        client.put(f"/api/v1/locations/{location_id}", json=update_data)
        
        # Verify the update
        get_response = client.get(f"/api/v1/locations/{location_id}")
        updated_location = get_response.json()
        assert updated_location["capacity"] == 10

    def test_delete_location_returns_204(self, client: TestClient):
        """Should delete location and return 204."""
        # Create a location
        location_data = {
            "name": "Temporary Area",
            "type": "common_area",
            "building": "West",
            "floor": 1,
            "capacity": 30
        }
        create_response = client.post("/api/v1/locations", json=location_data)
        created_location = create_response.json()
        location_id = created_location["id"]
        
        # Delete the location
        response = client.delete(f"/api/v1/locations/{location_id}")
        assert response.status_code == 204

    def test_delete_location_not_found(self, client: TestClient):
        """Should return 404 when trying to delete non-existent location."""
        response = client.delete("/api/v1/locations/nonexistent-id")
        assert response.status_code == 404
