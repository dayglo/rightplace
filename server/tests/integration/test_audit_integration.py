"""
Integration tests for Audit Service with real database.

Tests audit logging with actual database connection and migration.
"""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from app.db.database import get_connection, init_db
from app.db.repositories.audit_repo import AuditRepository
from app.models.audit import AuditAction
from app.services.audit_service import AuditService


@pytest.fixture
def test_db():
    """Create test database with migrations."""
    conn = get_connection(":memory:")

    # Run migrations
    init_db(conn)

    yield conn
    conn.close()


@pytest.fixture
def audit_service(test_db):
    """Create AuditService with real database."""
    repo = AuditRepository(test_db)
    return AuditService(repo)


def test_audit_service_with_real_db(audit_service):
    """Should log and retrieve audit entries with real database."""
    # Log some actions
    audit_service.log_action(
        user_id="officer-001",
        action=AuditAction.ROLLCALL_STARTED,
        entity_type="rollcall",
        entity_id="rc-001",
        details={"location": "A Wing"},
    )

    audit_service.log_action(
        user_id="officer-001",
        action=AuditAction.VERIFICATION_RECORDED,
        entity_type="verification",
        entity_id="ver-001",
        details={"confidence": 0.89},
    )

    # Retrieve audit trail
    history = audit_service.get_entity_history("rollcall", "rc-001")
    assert len(history) == 1
    assert history[0].action == AuditAction.ROLLCALL_STARTED.value
    assert history[0].details["location"] == "A Wing"


def test_audit_export_with_real_db(audit_service):
    """Should export audit logs to CSV format."""
    # Create some audit entries
    for i in range(3):
        audit_service.log_action(
            user_id=f"officer-{i}",
            action=AuditAction.INMATE_CREATED,
            entity_type="inmate",
            entity_id=f"inmate-{i}",
        )

    # Export as CSV
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now() + timedelta(hours=1)
    csv = audit_service.export_logs(start, end, format="csv")

    # Verify CSV contains entries
    lines = csv.strip().split("\n")
    assert len(lines) == 4  # Header + 3 entries
    assert "id,timestamp,user_id" in lines[0]


def test_migration_adds_audit_columns(test_db):
    """Should verify migration added ip_address and user_agent columns."""
    # Query table schema
    cursor = test_db.execute("PRAGMA table_info(audit_log)")
    columns = {row[1] for row in cursor.fetchall()}

    # Verify new columns exist
    assert "ip_address" in columns
    assert "user_agent" in columns
    assert "officer_id" in columns
    assert "details" in columns


def test_audit_indexes_created(test_db):
    """Should verify all required indexes were created."""
    cursor = test_db.execute("SELECT name FROM sqlite_master WHERE type='index'")
    indexes = {row[0] for row in cursor.fetchall()}

    # Verify audit indexes
    assert "idx_audit_timestamp" in indexes
    assert "idx_audit_action" in indexes
    assert "idx_audit_user" in indexes
    assert "idx_audit_entity" in indexes
