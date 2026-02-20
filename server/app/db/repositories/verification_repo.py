"""
Verification repository for database operations.

Handles CRUD operations for verification records.
"""
import sqlite3
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.verification import (
    Verification,
    VerificationStatus,
    ManualOverrideReason,
)


class VerificationRepository:
    """Repository for verification database operations."""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def create(
        self,
        roll_call_id: str,
        inmate_id: str,
        location_id: str,
        status: VerificationStatus,
        confidence: float,
        photo_uri: Optional[str] = None,
        is_manual_override: bool = False,
        manual_override_reason: Optional[ManualOverrideReason] = None,
        notes: str = "",
    ) -> Verification:
        """
        Create a new verification record.

        Args:
            roll_call_id: Roll call ID
            inmate_id: Inmate ID
            location_id: Location ID
            status: Verification status
            confidence: Confidence score
            photo_uri: Optional photo URI
            is_manual_override: Whether this is a manual override
            manual_override_reason: Reason for manual override
            notes: Additional notes

        Returns:
            Created verification with generated ID and timestamp
        """
        verification_id = str(uuid4())
        timestamp = datetime.now()

        self.conn.execute(
            """
            INSERT INTO verifications (
                id, roll_call_id, inmate_id, location_id,
                status, confidence, photo_uri, timestamp,
                is_manual_override, manual_override_reason, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                verification_id,
                roll_call_id,
                inmate_id,
                location_id,
                status.value,
                confidence,
                photo_uri,
                timestamp.isoformat(),
                1 if is_manual_override else 0,
                manual_override_reason.value if manual_override_reason else None,
                notes,
            ),
        )
        self.conn.commit()

        return self.get_by_id(verification_id)  # type: ignore

    def get_by_id(self, verification_id: str) -> Optional[Verification]:
        """
        Retrieve verification by ID.

        Args:
            verification_id: Verification ID

        Returns:
            Verification if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM verifications WHERE id = ?",
            (verification_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_verification(row)

    def get_by_roll_call(self, roll_call_id: str) -> list[Verification]:
        """
        Retrieve all verifications for a roll call.

        Args:
            roll_call_id: Roll call ID

        Returns:
            List of verifications for the specified roll call
        """
        cursor = self.conn.execute(
            "SELECT * FROM verifications WHERE roll_call_id = ? ORDER BY timestamp",
            (roll_call_id,),
        )
        rows = cursor.fetchall()

        return [self._row_to_verification(row) for row in rows]

    def get_by_roll_call_before_timestamp(
        self, roll_call_id: str, timestamp: datetime
    ) -> list[Verification]:
        """
        Retrieve verifications for a roll call before a specific timestamp.

        Args:
            roll_call_id: Roll call ID
            timestamp: Only return verifications before this time

        Returns:
            List of verifications for the specified roll call before the timestamp
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM verifications
            WHERE roll_call_id = ? AND timestamp <= ?
            ORDER BY timestamp
            """,
            (roll_call_id, timestamp.isoformat()),
        )
        rows = cursor.fetchall()

        return [self._row_to_verification(row) for row in rows]

    def get_by_inmate(self, inmate_id: str) -> list[Verification]:
        """
        Retrieve all verifications for an inmate.

        Args:
            inmate_id: Inmate ID

        Returns:
            List of verifications for the specified inmate
        """
        cursor = self.conn.execute(
            "SELECT * FROM verifications WHERE inmate_id = ? ORDER BY timestamp DESC",
            (inmate_id,),
        )
        rows = cursor.fetchall()

        return [self._row_to_verification(row) for row in rows]

    def get_by_location(self, location_id: str) -> list[Verification]:
        """
        Retrieve all verifications for a location.

        Args:
            location_id: Location ID

        Returns:
            List of verifications for the specified location
        """
        cursor = self.conn.execute(
            "SELECT * FROM verifications WHERE location_id = ? ORDER BY timestamp DESC",
            (location_id,),
        )
        rows = cursor.fetchall()

        return [self._row_to_verification(row) for row in rows]

    def count_by_roll_call(self, roll_call_id: str) -> int:
        """
        Count verifications for a roll call.

        Args:
            roll_call_id: Roll call ID

        Returns:
            Number of verifications
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM verifications WHERE roll_call_id = ?",
            (roll_call_id,),
        )
        return cursor.fetchone()[0]

    def count_by_status(
        self, roll_call_id: str, status: VerificationStatus
    ) -> int:
        """
        Count verifications by status for a roll call.

        Args:
            roll_call_id: Roll call ID
            status: Verification status

        Returns:
            Number of verifications with the specified status
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM verifications WHERE roll_call_id = ? AND status = ?",
            (roll_call_id, status.value),
        )
        return cursor.fetchone()[0]

    def get_manual_overrides(self, roll_call_id: str) -> list[Verification]:
        """
        Retrieve all manual override verifications for a roll call.

        Args:
            roll_call_id: Roll call ID

        Returns:
            List of manual override verifications
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM verifications 
            WHERE roll_call_id = ? AND is_manual_override = 1
            ORDER BY timestamp
            """,
            (roll_call_id,),
        )
        rows = cursor.fetchall()

        return [self._row_to_verification(row) for row in rows]

    def delete(self, verification_id: str) -> bool:
        """
        Delete verification record.

        Args:
            verification_id: Verification ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM verifications WHERE id = ?",
            (verification_id,),
        )
        self.conn.commit()

        return cursor.rowcount > 0

    def _row_to_verification(self, row: sqlite3.Row) -> Verification:
        """
        Convert database row to Verification model.

        Args:
            row: SQLite row

        Returns:
            Verification model instance
        """
        return Verification(
            id=row["id"],
            roll_call_id=row["roll_call_id"],
            inmate_id=row["inmate_id"],
            location_id=row["location_id"],
            status=VerificationStatus(row["status"]),
            confidence=row["confidence"],
            photo_uri=row["photo_uri"],
            timestamp=datetime.fromisoformat(row["timestamp"]),
            is_manual_override=bool(row["is_manual_override"]),
            manual_override_reason=(
                ManualOverrideReason(row["manual_override_reason"])
                if row["manual_override_reason"]
                else None
            ),
            notes=row["notes"] or "",
        )