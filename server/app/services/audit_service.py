"""
Audit service for business logic.

Handles audit logging and export functionality.
"""

import csv
import io
from datetime import datetime
from typing import Optional

from app.db.repositories.audit_repo import AuditRepository
from app.models.audit import AuditEntry, AuditAction


class AuditService:
    """Service for audit logging business logic."""

    def __init__(self, audit_repo: AuditRepository):
        """
        Initialize service with repository.

        Args:
            audit_repo: Audit repository
        """
        self.audit_repo = audit_repo

    def log_action(
        self,
        user_id: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> None:
        """
        Log an auditable action.

        Args:
            user_id: Officer/user ID who performed the action
            action: Type of action performed
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            details: Optional additional context
            ip_address: Optional IP address of the client
            user_agent: Optional user agent string
        """
        self.audit_repo.create(
            user_id=user_id,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
        )

    def get_entity_history(self, entity_type: str, entity_id: str) -> list[AuditEntry]:
        """
        Get audit trail for a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            List of audit entries in chronological order
        """
        return self.audit_repo.get_by_entity(entity_type, entity_id)

    def get_user_actions(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[AuditEntry]:
        """
        Get all actions by a user in a time range.

        Args:
            user_id: Officer/user ID
            start: Start of time range
            end: End of time range

        Returns:
            List of audit entries in chronological order
        """
        return self.audit_repo.get_by_user(user_id, start, end)

    def export_logs(self, start: datetime, end: datetime, format: str = "csv") -> str:
        """
        Export audit logs for a time period.

        Args:
            start: Start of time range
            end: End of time range
            format: Export format (currently only "csv" supported)

        Returns:
            Formatted export string

        Raises:
            ValueError: If unsupported format is specified
        """
        if format != "csv":
            raise ValueError(f"Unsupported format: {format}")

        # Get all entries in time range
        entries = self.audit_repo.get_all(start=start, end=end)

        # Reverse to chronological order (oldest first) for export
        entries.reverse()

        # Generate CSV
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=[
                "id",
                "timestamp",
                "user_id",
                "action",
                "entity_type",
                "entity_id",
                "details",
                "ip_address",
                "user_agent",
            ],
        )

        writer.writeheader()

        for entry in entries:
            writer.writerow(
                {
                    "id": entry.id,
                    "timestamp": entry.timestamp.isoformat(),
                    "user_id": entry.user_id,
                    "action": entry.action,
                    "entity_type": entry.entity_type,
                    "entity_id": entry.entity_id,
                    "details": str(entry.details) if entry.details else "",
                    "ip_address": entry.ip_address or "",
                    "user_agent": entry.user_agent or "",
                }
            )

        return output.getvalue()
