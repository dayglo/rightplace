"""Integration tests for inmates CRUD endpoints."""

import pytest
from fastapi.testclient import TestClient


class TestInmatesCRUD:
    """Test suite for inmates CRUD endpoints."""

    def test_create_inmate_returns_201(self, client: TestClient):
        """Should create a new inmate and return 201."""
        inmate_data = {
            "inmate_number": "A12345",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-15",
            "cell_block": "A",
            "cell_number": "101"
        }
        response = client.post("/api/v1/inmates", json=inmate_data)
        assert response.status_code == 201

    def test_create_inmate_response_structure(self, client: TestClient):
        """Should return complete inmate object with generated ID."""
        inmate_data = {
            "inmate_number": "A12346",
            "first_name": "Jane",
            "last_name": "Smith",
            "date_of_birth": "1985-05-20",
            "cell_block": "B",
            "cell_number": "202"
        }
        response = client.post("/api/v1/inmates", json=inmate_data)
        data = response.json()
        
        assert "id" in data
        assert data["inmate_number"] == "A12346"
        assert data["first_name"] == "Jane"
        assert data["last_name"] == "Smith"
        assert data["is_enrolled"] is False
        assert data["is_active"] is True

    def test_get_all_inmates_returns_200(self, client: TestClient):
        """Should return list of all inmates."""
        response = client.get("/api/v1/inmates")
        assert response.status_code == 200

    def test_get_all_inmates_returns_list(self, client: TestClient):
        """Should return a list (even if empty)."""
        response = client.get("/api/v1/inmates")
        data = response.json()
        assert isinstance(data, list)

    def test_get_inmate_by_id_returns_200(self, client: TestClient):
        """Should return inmate when valid ID provided."""
        # First create an inmate
        inmate_data = {
            "inmate_number": "A12347",
            "first_name": "Bob",
            "last_name": "Johnson",
            "date_of_birth": "1992-03-10",
            "cell_block": "C",
            "cell_number": "303"
        }
        create_response = client.post("/api/v1/inmates", json=inmate_data)
        created_inmate = create_response.json()
        inmate_id = created_inmate["id"]
        
        # Then get it by ID
        response = client.get(f"/api/v1/inmates/{inmate_id}")
        assert response.status_code == 200

    def test_get_inmate_by_id_not_found(self, client: TestClient):
        """Should return 404 when inmate doesn't exist."""
        response = client.get("/api/v1/inmates/nonexistent-id")
        assert response.status_code == 404

    def test_update_inmate_returns_200(self, client: TestClient):
        """Should update inmate and return 200."""
        # Create an inmate
        inmate_data = {
            "inmate_number": "A12348",
            "first_name": "Alice",
            "last_name": "Brown",
            "date_of_birth": "1988-07-25",
            "cell_block": "D",
            "cell_number": "404"
        }
        create_response = client.post("/api/v1/inmates", json=inmate_data)
        created_inmate = create_response.json()
        inmate_id = created_inmate["id"]
        
        # Update the inmate
        update_data = {
            "cell_block": "E",
            "cell_number": "505"
        }
        response = client.put(f"/api/v1/inmates/{inmate_id}", json=update_data)
        assert response.status_code == 200

    def test_update_inmate_changes_data(self, client: TestClient):
        """Should actually update the inmate data."""
        # Create an inmate
        inmate_data = {
            "inmate_number": "A12349",
            "first_name": "Charlie",
            "last_name": "Davis",
            "date_of_birth": "1995-11-30",
            "cell_block": "F",
            "cell_number": "606"
        }
        create_response = client.post("/api/v1/inmates", json=inmate_data)
        created_inmate = create_response.json()
        inmate_id = created_inmate["id"]
        
        # Update the inmate
        update_data = {
            "cell_block": "G",
            "cell_number": "707"
        }
        client.put(f"/api/v1/inmates/{inmate_id}", json=update_data)
        
        # Verify the update
        get_response = client.get(f"/api/v1/inmates/{inmate_id}")
        updated_inmate = get_response.json()
        assert updated_inmate["cell_block"] == "G"
        assert updated_inmate["cell_number"] == "707"

    def test_delete_inmate_returns_204(self, client: TestClient):
        """Should delete inmate and return 204."""
        # Create an inmate
        inmate_data = {
            "inmate_number": "A12350",
            "first_name": "David",
            "last_name": "Wilson",
            "date_of_birth": "1991-09-05",
            "cell_block": "H",
            "cell_number": "808"
        }
        create_response = client.post("/api/v1/inmates", json=inmate_data)
        created_inmate = create_response.json()
        inmate_id = created_inmate["id"]
        
        # Delete the inmate
        response = client.delete(f"/api/v1/inmates/{inmate_id}")
        assert response.status_code == 204

    def test_delete_inmate_not_found(self, client: TestClient):
        """Should return 404 when trying to delete non-existent inmate."""
        response = client.delete("/api/v1/inmates/nonexistent-id")
        assert response.status_code == 404
