"""
Audit log repository for database operations.

Handles creation and querying of audit trail entries.
Note: Audit entries are immutable - no update or delete operations.
"""

import json
import sqlite3
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.audit import AuditEntry, AuditAction


class AuditRepository:
    """Repository for audit log database operations."""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def create(
        self,
        user_id: str,
        action: AuditAction,
        entity_type: str,
        entity_id: str,
        details: Optional[dict] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> str:
        """
        Create a new audit log entry.

        Args:
            user_id: Officer/user ID who performed the action
            action: Type of action performed
            entity_type: Type of entity affected
            entity_id: ID of entity affected
            details: Optional JSON details about the action
            ip_address: Optional IP address of the client
            user_agent: Optional user agent string

        Returns:
            ID of created audit entry
        """
        entry_id = str(uuid4())
        timestamp = datetime.now()

        # Serialize details to JSON if provided
        details_json = json.dumps(details) if details else None

        self.conn.execute(
            """
            INSERT INTO audit_log (
                id, timestamp, officer_id, action,
                entity_type, entity_id, details,
                ip_address, user_agent
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                timestamp.isoformat(),
                user_id,
                action.value,
                entity_type,
                entity_id,
                details_json,
                ip_address,
                user_agent,
            ),
        )
        self.conn.commit()

        return entry_id

    def get_by_id(self, entry_id: str) -> Optional[AuditEntry]:
        """
        Retrieve audit entry by ID.

        Args:
            entry_id: Audit entry ID

        Returns:
            AuditEntry if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM audit_log WHERE id = ?",
            (entry_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_entry(row)

    def get_by_entity(self, entity_type: str, entity_id: str) -> list[AuditEntry]:
        """
        Retrieve all audit entries for a specific entity.

        Args:
            entity_type: Type of entity
            entity_id: Entity ID

        Returns:
            List of audit entries in chronological order
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM audit_log
            WHERE entity_type = ? AND entity_id = ?
            ORDER BY timestamp ASC
            """,
            (entity_type, entity_id),
        )
        rows = cursor.fetchall()

        return [self._row_to_entry(row) for row in rows]

    def get_by_user(
        self, user_id: str, start: datetime, end: datetime
    ) -> list[AuditEntry]:
        """
        Retrieve all actions by a user in a time range.

        Args:
            user_id: Officer/user ID
            start: Start of time range (inclusive)
            end: End of time range (inclusive)

        Returns:
            List of audit entries in chronological order
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM audit_log
            WHERE officer_id = ?
              AND timestamp >= ?
              AND timestamp <= ?
            ORDER BY timestamp ASC
            """,
            (user_id, start.isoformat(), end.isoformat()),
        )
        rows = cursor.fetchall()

        return [self._row_to_entry(row) for row in rows]

    def get_by_action(self, action: AuditAction) -> list[AuditEntry]:
        """
        Retrieve all entries of a specific action type.

        Args:
            action: Action type to filter by

        Returns:
            List of audit entries in chronological order
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM audit_log
            WHERE action = ?
            ORDER BY timestamp ASC
            """,
            (action.value,),
        )
        rows = cursor.fetchall()

        return [self._row_to_entry(row) for row in rows]

    def get_all(
        self,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        limit: Optional[int] = None,
    ) -> list[AuditEntry]:
        """
        Retrieve all audit entries with optional filtering.

        Args:
            start: Optional start of time range
            end: Optional end of time range
            limit: Optional maximum number of entries to return

        Returns:
            List of audit entries in reverse chronological order (newest first)
        """
        query = "SELECT * FROM audit_log"
        params = []

        # Add time range filters if provided
        conditions = []
        if start:
            conditions.append("timestamp >= ?")
            params.append(start.isoformat())
        if end:
            conditions.append("timestamp <= ?")
            params.append(end.isoformat())

        if conditions:
            query += " WHERE " + " AND ".join(conditions)

        query += " ORDER BY timestamp DESC"

        if limit:
            query += " LIMIT ?"
            params.append(limit)

        cursor = self.conn.execute(query, params)
        rows = cursor.fetchall()

        return [self._row_to_entry(row) for row in rows]

    def _row_to_entry(self, row: sqlite3.Row) -> AuditEntry:
        """
        Convert database row to AuditEntry model.

        Args:
            row: SQLite row

        Returns:
            AuditEntry model instance
        """
        # Parse details JSON if present
        details = None
        if row["details"]:
            details = json.loads(row["details"])

        return AuditEntry(
            id=row["id"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            user_id=row["officer_id"],
            action=row["action"],
            entity_type=row["entity_type"],
            entity_id=row["entity_id"],
            details=details,
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
        )
