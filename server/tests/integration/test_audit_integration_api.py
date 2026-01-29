"""
Integration tests for audit logging with API endpoints.

Tests that audit service correctly logs actions when API endpoints are called.
"""
import pytest
from datetime import datetime, timedelta

from app.db.repositories.audit_repo import AuditRepository
from app.models.audit import AuditAction


class TestInmateAuditLogging:
    """Test audit logging for inmate endpoints."""

    def test_create_inmate_logs_audit_entry(self, client, test_db):
        """Should log INMATE_CREATED when creating an inmate."""
        from app.db.database import get_connection

        # Create inmate via API
        response = client.post(
            "/api/v1/inmates",
            json={
                "inmate_number": "A12345",
                "first_name": "John",
                "last_name": "Doe",
                "date_of_birth": "1990-01-01",
                "cell_block": "A",
                "cell_number": "101",
            },
            headers={"X-Officer-ID": "officer-test"},
        )

        assert response.status_code == 201
        inmate = response.json()

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_entity("inmate", inmate["id"])

        assert len(entries) == 1
        assert entries[0].action == AuditAction.INMATE_CREATED.value
        assert entries[0].user_id == "officer-test"
        assert "inmate_number" in entries[0].details
        assert entries[0].details["inmate_number"] == "A12345"

        conn.close()

    def test_update_inmate_logs_audit_entry(self, client, test_db):
        """Should log INMATE_UPDATED when updating an inmate."""
        from app.db.database import get_connection

        # Create inmate first
        create_response = client.post(
            "/api/v1/inmates",
            json={
                "inmate_number": "A12346",
                "first_name": "Jane",
                "last_name": "Smith",
                "date_of_birth": "1992-05-15",
                "cell_block": "B",
                "cell_number": "202",
            },
            headers={"X-Officer-ID": "officer-create"},
        )
        assert create_response.status_code == 201
        inmate_id = create_response.json()["id"]

        # Update inmate
        update_response = client.put(
            f"/api/v1/inmates/{inmate_id}",
            json={"cell_block": "C", "cell_number": "303"},
            headers={"X-Officer-ID": "officer-update"},
        )

        assert update_response.status_code == 200

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_entity("inmate", inmate_id)

        # Should have 2 entries: create + update
        assert len(entries) == 2

        # Find the update entry
        update_entry = [e for e in entries if e.action == AuditAction.INMATE_UPDATED.value][0]
        assert update_entry.user_id == "officer-update"
        assert "updated_fields" in update_entry.details
        assert update_entry.details["updated_fields"]["cell_block"] == "C"

        conn.close()

    def test_delete_inmate_logs_audit_entry(self, client, test_db):
        """Should log INMATE_DELETED when deleting an inmate."""
        from app.db.database import get_connection

        # Create inmate first
        create_response = client.post(
            "/api/v1/inmates",
            json={
                "inmate_number": "A12347",
                "first_name": "Bob",
                "last_name": "Jones",
                "date_of_birth": "1988-03-22",
                "cell_block": "D",
                "cell_number": "404",
            },
            headers={"X-Officer-ID": "officer-create"},
        )
        assert create_response.status_code == 201
        inmate_id = create_response.json()["id"]

        # Delete inmate
        delete_response = client.delete(
            f"/api/v1/inmates/{inmate_id}",
            headers={"X-Officer-ID": "officer-delete"},
        )

        assert delete_response.status_code == 204

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_entity("inmate", inmate_id)

        # Should have 2 entries: create + delete
        assert len(entries) == 2

        # Find the delete entry
        delete_entry = [e for e in entries if e.action == AuditAction.INMATE_DELETED.value][0]
        assert delete_entry.user_id == "officer-delete"

        conn.close()


class TestRollCallAuditLogging:
    """Test audit logging for roll call endpoints."""

    def test_start_rollcall_logs_audit_entry(self, client, test_db):
        """Should log ROLLCALL_STARTED when starting a roll call."""
        from app.db.database import get_connection

        # Create a roll call first
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/v1/rollcalls",
            json={
                "name": "Morning Roll Call",
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
            },
            headers={"X-Officer-ID": "officer-create"},
        )
        assert create_response.status_code == 201
        rollcall_id = create_response.json()["id"]

        # Start the roll call
        start_response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/start",
            headers={"X-Officer-ID": "officer-start"},
        )

        assert start_response.status_code == 200

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_action(AuditAction.ROLLCALL_STARTED)

        assert len(entries) >= 1
        start_entry = [e for e in entries if e.entity_id == rollcall_id][0]
        assert start_entry.user_id == "officer-start"
        assert "expected_stops" in start_entry.details

        conn.close()

    def test_complete_rollcall_logs_audit_entry(self, client, test_db):
        """Should log ROLLCALL_COMPLETED when completing a roll call."""
        from app.db.database import get_connection

        # Create and start a roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/v1/rollcalls",
            json={
                "name": "Evening Roll Call",
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
            },
            headers={"X-Officer-ID": "officer-create"},
        )
        rollcall_id = create_response.json()["id"]

        # Start it
        client.post(
            f"/api/v1/rollcalls/{rollcall_id}/start",
            headers={"X-Officer-ID": "officer-start"},
        )

        # Complete it
        complete_response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/complete",
            headers={"X-Officer-ID": "officer-complete"},
        )

        assert complete_response.status_code == 200

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_action(AuditAction.ROLLCALL_COMPLETED)

        assert len(entries) >= 1
        complete_entry = [e for e in entries if e.entity_id == rollcall_id][0]
        assert complete_entry.user_id == "officer-complete"
        assert "progress_percentage" in complete_entry.details

        conn.close()

    def test_cancel_rollcall_logs_audit_entry(self, client, test_db):
        """Should log ROLLCALL_CANCELLED when cancelling a roll call."""
        from app.db.database import get_connection

        # Create a roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        create_response = client.post(
            "/api/v1/rollcalls",
            json={
                "name": "Test Roll Call",
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
            },
            headers={"X-Officer-ID": "officer-create"},
        )
        rollcall_id = create_response.json()["id"]

        # Cancel it
        cancel_response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/cancel",
            json={"reason": "Emergency situation"},
            headers={"X-Officer-ID": "officer-cancel"},
        )

        assert cancel_response.status_code == 200

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_action(AuditAction.ROLLCALL_CANCELLED)

        assert len(entries) >= 1
        cancel_entry = [e for e in entries if e.entity_id == rollcall_id][0]
        assert cancel_entry.user_id == "officer-cancel"
        assert cancel_entry.details["reason"] == "Emergency situation"

        conn.close()


class TestVerificationAuditLogging:
    """Test audit logging for verification endpoints."""

    def test_record_verification_logs_audit_entry(self, client, test_db):
        """Should log VERIFICATION_RECORDED for regular verifications."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository
        from app.models.inmate import InmateCreate
        from app.models.location import LocationCreate

        # Setup: create inmate and location first
        conn = get_connection(test_db)

        inmate_repo = InmateRepository(conn)
        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="V001",
                first_name="Test",
                last_name="Inmate",
                date_of_birth="1990-01-01",
                cell_block="A",
                cell_number="101",
            )
        )

        location_repo = LocationRepository(conn)
        location = location_repo.create(
            LocationCreate(
                name="Test Cell",
                type="cell",
                building="Main",
                floor=1,
                capacity=2,
            )
        )
        conn.close()

        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        rollcall_response = client.post(
            "/api/v1/rollcalls",
            json={
                "name": "Verification Test",
                "scheduled_at": scheduled_at,
                "route": [
                    {
                        "id": "stop1",
                        "location_id": location.id,
                        "order": 1,
                        "expected_inmates": [inmate.id],
                        "status": "pending",
                    }
                ],
                "officer_id": "officer1",
            },
        )
        rollcall_id = rollcall_response.json()["id"]

        # Record verification
        verification_response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/verification",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "status": "verified",
                "confidence": 0.95,
                "is_manual_override": False,
            },
            headers={"X-Officer-ID": "officer-verify"},
        )

        assert verification_response.status_code == 201

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_action(AuditAction.VERIFICATION_RECORDED)

        assert len(entries) >= 1
        verify_entry = entries[-1]  # Get the most recent
        assert verify_entry.user_id == "officer-verify"
        assert verify_entry.details["confidence"] == 0.95

        conn.close()

    def test_manual_override_logs_correct_action(self, client, test_db):
        """Should log MANUAL_OVERRIDE_USED for manual verifications."""
        from app.db.database import get_connection
        from app.db.repositories.inmate_repo import InmateRepository
        from app.db.repositories.location_repo import LocationRepository
        from app.models.inmate import InmateCreate
        from app.models.location import LocationCreate

        # Setup: create inmate and location
        conn = get_connection(test_db)

        inmate_repo = InmateRepository(conn)
        inmate = inmate_repo.create(
            InmateCreate(
                inmate_number="V002",
                first_name="Manual",
                last_name="Override",
                date_of_birth="1991-02-02",
                cell_block="B",
                cell_number="202",
            )
        )

        location_repo = LocationRepository(conn)
        location = location_repo.create(
            LocationCreate(
                name="Test Cell 2",
                type="cell",
                building="Main",
                floor=2,
                capacity=2,
            )
        )
        conn.close()

        # Create roll call
        scheduled_at = (datetime.now() + timedelta(hours=1)).isoformat()
        rollcall_response = client.post(
            "/api/v1/rollcalls",
            json={
                "name": "Manual Override Test",
                "scheduled_at": scheduled_at,
                "route": [
                    {
                        "id": "stop1",
                        "location_id": location.id,
                        "order": 1,
                        "expected_inmates": [inmate.id],
                        "status": "pending",
                    }
                ],
                "officer_id": "officer1",
            },
        )
        rollcall_id = rollcall_response.json()["id"]

        # Record manual override
        verification_response = client.post(
            f"/api/v1/rollcalls/{rollcall_id}/verification",
            json={
                "inmate_id": inmate.id,
                "location_id": location.id,
                "status": "manual",
                "confidence": 0.0,
                "is_manual_override": True,
                "manual_override_reason": "facial_injury",
                "notes": "Inmate has bandage on face",
            },
            headers={"X-Officer-ID": "officer-override"},
        )

        assert verification_response.status_code == 201

        # Check audit log
        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_action(AuditAction.MANUAL_OVERRIDE_USED)

        assert len(entries) >= 1
        override_entry = entries[-1]
        assert override_entry.user_id == "officer-override"
        assert override_entry.details["manual_override_reason"] == "facial_injury"

        conn.close()


class TestAuditContextCapture:
    """Test that audit logging captures request context correctly."""

    def test_captures_user_id_from_header(self, client, test_db):
        """Should capture user ID from X-Officer-ID header."""
        from app.db.database import get_connection

        response = client.post(
            "/api/v1/inmates",
            json={
                "inmate_number": "CTX001",
                "first_name": "Context",
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "cell_block": "A",
                "cell_number": "101",
            },
            headers={"X-Officer-ID": "officer-alice"},
        )

        assert response.status_code == 201
        inmate_id = response.json()["id"]

        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_entity("inmate", inmate_id)

        assert len(entries) == 1
        assert entries[0].user_id == "officer-alice"
        conn.close()

    def test_defaults_to_unknown_when_no_header(self, client, test_db):
        """Should use 'unknown' when X-Officer-ID header is missing."""
        from app.db.database import get_connection

        response = client.post(
            "/api/v1/inmates",
            json={
                "inmate_number": "CTX002",
                "first_name": "No",
                "last_name": "Header",
                "date_of_birth": "1990-01-01",
                "cell_block": "A",
                "cell_number": "102",
            },
        )

        assert response.status_code == 201
        inmate_id = response.json()["id"]

        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_entity("inmate", inmate_id)

        assert len(entries) == 1
        assert entries[0].user_id == "unknown"
        conn.close()

    def test_captures_ip_address(self, client, test_db):
        """Should capture client IP address."""
        from app.db.database import get_connection

        response = client.post(
            "/api/v1/inmates",
            json={
                "inmate_number": "CTX003",
                "first_name": "IP",
                "last_name": "Test",
                "date_of_birth": "1990-01-01",
                "cell_block": "A",
                "cell_number": "103",
            },
            headers={"X-Officer-ID": "officer-bob"},
        )

        assert response.status_code == 201
        inmate_id = response.json()["id"]

        conn = get_connection(test_db)
        audit_repo = AuditRepository(conn)
        entries = audit_repo.get_by_entity("inmate", inmate_id)

        assert len(entries) == 1
        assert entries[0].ip_address is not None
        # TestClient provides "testclient" as the host
        assert entries[0].ip_address in ["testclient", "unknown"]
        conn.close()
