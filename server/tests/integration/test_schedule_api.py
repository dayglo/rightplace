"""
Integration tests for schedule API endpoints.

Tests REST API for schedule management with proper HTTP status codes.
"""
from datetime import date

import pytest

from app.models.inmate import InmateCreate
from app.models.location import LocationCreate, LocationType
from app.models.schedule import ActivityType


class TestScheduleAPICreate:
    """Tests for POST /api/v1/schedules (create)."""

    def test_create_schedule_entry_success(self, client, test_db):
        """Should return 201 with created entry."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup: create inmate and location
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create schedule entry
        response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )

        assert response.status_code == 201
        data = response.json()
        assert data["inmate_id"] == inmate.id
        assert data["location_id"] == location.id
        assert data["day_of_week"] == 1
        assert data["start_time"] == "09:00"
        assert data["end_time"] == "12:00"
        assert data["activity_type"] == "work"
        assert "id" in data
        assert "created_at" in data

    def test_create_schedule_entry_invalid_inmate(self, client, test_db):
        """Should return 400 for unknown inmate."""
        from app.db.database import get_connection
        from app.db.repositories.location_repo import LocationRepository

        # Setup: create location only
        conn = get_connection(test_db)
        location_repo = LocationRepository(conn)
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": "nonexistent-inmate-id",
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_schedule_entry_invalid_location(self, client, test_db):
        """Should return 400 for unknown location."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository

        # Setup: create inmate only
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        conn.close()

        response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": "nonexistent-location-id",
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )

        assert response.status_code == 400
        assert "not found" in response.json()["detail"].lower()

    def test_create_schedule_entry_conflict(self, client, test_db):
        """Should return 409 for scheduling conflict."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create first entry
        client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )

        # Try to create overlapping entry
        response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "10:00",  # Overlaps!
                "end_time": "13:00",
                "activity_type": "education",
            },
        )

        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()

    def test_create_schedule_entry_validation_error(self, client, test_db):
        """Should return 422 for invalid data (bad time format, etc.)."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Invalid time format
        response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "9:00",  # Missing leading zero
                "end_time": "12:00",
                "activity_type": "work",
            },
        )

        assert response.status_code == 422

    def test_create_schedule_entry_end_before_start(self, client, test_db):
        """Should return 422 when end_time before start_time."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "12:00",
                "end_time": "09:00",  # Before start!
                "activity_type": "work",
            },
        )

        assert response.status_code == 422


class TestScheduleAPIRead:
    """Tests for GET /api/v1/schedules endpoints."""

    def test_get_schedule_entry_success(self, client, test_db):
        """Should return 200 with entry."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup and create entry
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create entry
        create_response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )
        entry_id = create_response.json()["id"]

        # Get entry
        response = client.get(f"/api/v1/schedules/{entry_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == entry_id
        assert data["inmate_id"] == inmate.id

    def test_get_schedule_entry_not_found(self, client):
        """Should return 404 for unknown entry."""
        response = client.get("/api/v1/schedules/nonexistent-id")
        assert response.status_code == 404

    def test_list_inmate_schedules(self, client, test_db):
        """Should return 200 with all entries for inmate."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create multiple entries
        for day in range(3):
            client.post(
                "/api/v1/schedules",
                json={
                    "inmate_id": inmate.id,
                    "location_id": location.id,
                    "day_of_week": day,
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "activity_type": "work",
                },
            )

        # Get all entries for inmate
        response = client.get(f"/api/v1/schedules/inmate/{inmate.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 3
        assert all(e["inmate_id"] == inmate.id for e in data)

    def test_list_location_schedules(self, client, test_db):
        """Should return 200 with all entries for location."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate1 = inmate_repo.create(
            InmateCreate(
                inmate_number="A11111",
                first_name="Alice",
                last_name="Smith",
                date_of_birth=date(1991, 5, 10),
                cell_block="A",
                cell_number="201",
            )
        )
        inmate2 = inmate_repo.create(
            InmateCreate(
                inmate_number="A22222",
                first_name="Bob",
                last_name="Jones",
                date_of_birth=date(1992, 8, 22),
                cell_block="B",
                cell_number="102",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create entries for both inmates at same location
        client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate1.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )
        client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate2.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "14:00",
                "end_time": "16:00",
                "activity_type": "work",
            },
        )

        # Get all entries for location
        response = client.get(f"/api/v1/schedules/location/{location.id}")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert all(e["location_id"] == location.id for e in data)

    def test_list_location_schedules_with_day_filter(self, client, test_db):
        """Should filter location schedule by day."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create entries on different days
        client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )
        client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 2,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )

        # Filter by day 1
        response = client.get(f"/api/v1/schedules/location/{location.id}?day_of_week=1")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["day_of_week"] == 1


class TestScheduleAPIUpdate:
    """Tests for PUT /api/v1/schedules/{id} (update)."""

    def test_update_schedule_entry_success(self, client, test_db):
        """Should return 200 with updated entry."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location1 = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        location2 = location_repo.create(
            LocationCreate(
                name="Library",
                type=LocationType.EDUCATION,
                building="East Block",
                floor=2,
                capacity=30,
            )
        )
        conn.close()

        # Create entry
        create_response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location1.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )
        entry_id = create_response.json()["id"]

        # Update location
        response = client.put(
            f"/api/v1/schedules/{entry_id}",
            json={"location_id": location2.id},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["location_id"] == location2.id
        # Other fields unchanged
        assert data["start_time"] == "09:00"

    def test_update_schedule_entry_not_found(self, client):
        """Should return 404 for unknown entry."""
        response = client.put(
            "/api/v1/schedules/nonexistent-id",
            json={"start_time": "10:00"},
        )
        assert response.status_code == 404

    def test_update_schedule_entry_conflict(self, client, test_db):
        """Should return 409 for conflict."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create two entries
        entry1_response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )
        entry2_response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "14:00",
                "end_time": "16:00",
                "activity_type": "education",
            },
        )
        entry2_id = entry2_response.json()["id"]

        # Try to update entry2 to overlap with entry1
        response = client.put(
            f"/api/v1/schedules/{entry2_id}",
            json={"start_time": "10:00", "end_time": "15:00"},
        )

        assert response.status_code == 409
        assert "conflict" in response.json()["detail"].lower()


class TestScheduleAPIDelete:
    """Tests for DELETE /api/v1/schedules/{id}."""

    def test_delete_schedule_entry_success(self, client, test_db):
        """Should return 204 on successful delete."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository

        # Setup
        conn = get_connection(test_db)
        inmate_repo = InmateRepository(conn)
        location_repo = LocationRepository(conn)

        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="A12345",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 15),
                cell_block="A",
                cell_number="101",
            )
        )
        location = location_repo.create(
            LocationCreate(
                name="Workshop A",
                type=LocationType.WORKSHOP,
                building="Main Block",
                floor=1,
                capacity=20,
            )
        )
        conn.close()

        # Create entry
        create_response = client.post(
            "/api/v1/schedules",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "day_of_week": 1,
                "start_time": "09:00",
                "end_time": "12:00",
                "activity_type": "work",
            },
        )
        entry_id = create_response.json()["id"]

        # Delete
        response = client.delete(f"/api/v1/schedules/{entry_id}")

        assert response.status_code == 204

        # Verify deleted
        get_response = client.get(f"/api/v1/schedules/{entry_id}")
        assert get_response.status_code == 404

    def test_delete_schedule_entry_not_found(self, client):
        """Should return 404 for unknown entry."""
        response = client.delete("/api/v1/schedules/nonexistent-id")
        assert response.status_code == 404
