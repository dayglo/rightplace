#!/usr/bin/env python3
"""
Demonstration of the Audit Service.

This script shows how to use the audit logging system to track actions
in the Prison Roll Call application.
"""
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.database import get_connection, init_db
from app.db.repositories.audit_repo import AuditRepository
from app.models.audit import AuditAction
from app.services.audit_service import AuditService


def demo_audit_logging():
    """Demonstrate audit logging functionality."""
    print("Prison Roll Call - Audit Service Demo")
    print("=" * 50)

    # Create in-memory database for demo
    print("\n1. Initializing database...")
    conn = get_connection(":memory:")
    init_db(conn)

    # Create audit service
    audit_repo = AuditRepository(conn)
    audit_service = AuditService(audit_repo)

    # Log various actions
    print("\n2. Logging roll call actions...")

    audit_service.log_action(
        user_id="officer-smith",
        action=AuditAction.ROLLCALL_STARTED,
        entity_type="rollcall",
        entity_id="rc-morning-001",
        details={
            "location": "A Wing",
            "scheduled_time": "08:00",
            "expected_inmates": 42,
        },
        ip_address="192.168.1.100",
        user_agent="PrisonRollCallApp/1.0 (Android)",
    )

    audit_service.log_action(
        user_id="officer-smith",
        action=AuditAction.VERIFICATION_RECORDED,
        entity_type="verification",
        entity_id="ver-001",
        details={
            "inmate_id": "inmate-123",
            "confidence": 0.89,
            "location": "Cell A1-01",
        },
    )

    audit_service.log_action(
        user_id="officer-smith",
        action=AuditAction.MANUAL_OVERRIDE_USED,
        entity_type="verification",
        entity_id="ver-002",
        details={
            "inmate_id": "inmate-456",
            "reason": "facial_injury",
            "notes": "Inmate has bandaging from medical treatment",
        },
    )

    audit_service.log_action(
        user_id="officer-smith",
        action=AuditAction.ROLLCALL_COMPLETED,
        entity_type="rollcall",
        entity_id="rc-morning-001",
        details={
            "duration_seconds": 720,
            "verified_count": 40,
            "manual_overrides": 2,
        },
    )

    # Retrieve audit history for roll call
    print("\n3. Retrieving roll call audit history...")
    history = audit_service.get_entity_history("rollcall", "rc-morning-001")

    print(f"\nRoll Call rc-morning-001 has {len(history)} audit entries:")
    for entry in history:
        print(f"  - {entry.timestamp.strftime('%H:%M:%S')}: {entry.action}")
        if entry.details:
            print(f"    Details: {entry.details}")

    # Get all actions by officer
    print("\n4. Retrieving officer actions...")
    start = datetime.now() - timedelta(hours=1)
    end = datetime.now() + timedelta(hours=1)
    officer_actions = audit_service.get_user_actions("officer-smith", start, end)

    print(f"\nOfficer smith performed {len(officer_actions)} actions:")
    for action in officer_actions:
        print(f"  - {action.action} on {action.entity_type} {action.entity_id}")

    # Export audit logs
    print("\n5. Exporting audit logs to CSV...")
    csv_export = audit_service.export_logs(start, end, format="csv")

    print("\nCSV Export (first 300 chars):")
    print(csv_export[:300] + "...")

    # Count lines
    line_count = len(csv_export.strip().split("\n")) - 1  # Subtract header
    print(f"\nTotal entries exported: {line_count}")

    # Demo: Query manual overrides
    print("\n6. Querying manual overrides...")
    manual_overrides = audit_repo.get_by_action(AuditAction.MANUAL_OVERRIDE_USED)

    print(f"\nFound {len(manual_overrides)} manual override(s):")
    for override in manual_overrides:
        print(f"  - Inmate: {override.details['inmate_id']}")
        print(f"    Reason: {override.details['reason']}")
        print(f"    Officer: {override.user_id}")

    print("\n" + "=" * 50)
    print("Demo complete!")

    conn.close()


if __name__ == "__main__":
    demo_audit_logging()
