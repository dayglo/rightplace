"""
Roll Call repository for database operations.

Handles CRUD operations for roll call records.
"""
import json
import sqlite3
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.rollcall import (
    RollCall,
    RollCallCreate,
    RollCallStatus,
    RouteStop,
)


class RollCallRepository:
    """Repository for roll call database operations."""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def create(self, rollcall_data: RollCallCreate) -> RollCall:
        """
        Create a new roll call record.

        Args:
            rollcall_data: Roll call creation data

        Returns:
            Created roll call with generated ID and timestamps
        """
        rollcall_id = str(uuid4())

        # Serialize route to JSON
        route_json = json.dumps([stop.model_dump() for stop in rollcall_data.route])

        self.conn.execute(
            """
            INSERT INTO roll_calls (
                id, name, status, scheduled_at, route,
                officer_id, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rollcall_id,
                rollcall_data.name,
                RollCallStatus.SCHEDULED.value,
                rollcall_data.scheduled_at.isoformat(),
                route_json,
                rollcall_data.officer_id,
                rollcall_data.notes,
            ),
        )
        self.conn.commit()

        return self.get_by_id(rollcall_id)  # type: ignore

    def get_by_id(self, rollcall_id: str) -> Optional[RollCall]:
        """
        Retrieve roll call by ID.

        Args:
            rollcall_id: Roll call ID

        Returns:
            Roll call if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM roll_calls WHERE id = ?",
            (rollcall_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_rollcall(row)

    def get_all(self) -> list[RollCall]:
        """
        Retrieve all roll calls.

        Returns:
            List of all roll calls
        """
        cursor = self.conn.execute(
            "SELECT * FROM roll_calls ORDER BY scheduled_at DESC"
        )
        rows = cursor.fetchall()

        return [self._row_to_rollcall(row) for row in rows]

    def get_by_status(self, status: RollCallStatus) -> list[RollCall]:
        """
        Retrieve roll calls by status.

        Args:
            status: Roll call status

        Returns:
            List of roll calls with the specified status
        """
        cursor = self.conn.execute(
            "SELECT * FROM roll_calls WHERE status = ? ORDER BY scheduled_at",
            (status.value,),
        )
        rows = cursor.fetchall()

        return [self._row_to_rollcall(row) for row in rows]

    def get_by_officer(self, officer_id: str) -> list[RollCall]:
        """
        Retrieve roll calls by officer.

        Args:
            officer_id: Officer ID

        Returns:
            List of roll calls for the specified officer
        """
        cursor = self.conn.execute(
            "SELECT * FROM roll_calls WHERE officer_id = ? ORDER BY scheduled_at DESC",
            (officer_id,),
        )
        rows = cursor.fetchall()

        return [self._row_to_rollcall(row) for row in rows]

    def update_status(
        self,
        rollcall_id: str,
        status: RollCallStatus,
        cancelled_reason: Optional[str] = None,
    ) -> Optional[RollCall]:
        """
        Update roll call status.

        Args:
            rollcall_id: Roll call ID
            status: New status
            cancelled_reason: Reason for cancellation (if applicable)

        Returns:
            Updated roll call if found, None otherwise
        """
        # Check if roll call exists
        existing = self.get_by_id(rollcall_id)
        if existing is None:
            return None

        # Update status and timestamps
        updates = ["status = ?"]
        params = [status.value]

        if status == RollCallStatus.IN_PROGRESS:
            updates.append("started_at = ?")
            params.append(datetime.now().isoformat())
        elif status == RollCallStatus.COMPLETED:
            updates.append("completed_at = ?")
            params.append(datetime.now().isoformat())
        elif status == RollCallStatus.CANCELLED:
            updates.append("cancelled_reason = ?")
            params.append(cancelled_reason)

        params.append(rollcall_id)

        query = f"UPDATE roll_calls SET {', '.join(updates)} WHERE id = ?"
        self.conn.execute(query, params)
        self.conn.commit()

        return self.get_by_id(rollcall_id)

    def update_route_stop(
        self,
        rollcall_id: str,
        stop_id: str,
        status: str,
        skip_reason: Optional[str] = None,
    ) -> Optional[RollCall]:
        """
        Update route stop status.

        Args:
            rollcall_id: Roll call ID
            stop_id: Stop ID
            status: New stop status
            skip_reason: Reason for skipping (if applicable)

        Returns:
            Updated roll call if found, None otherwise
        """
        rollcall = self.get_by_id(rollcall_id)
        if rollcall is None:
            return None

        # Update route stop
        updated_route = []
        for stop in rollcall.route:
            if stop.id == stop_id:
                stop_dict = stop.model_dump()
                stop_dict["status"] = status
                if status == "completed":
                    stop_dict["completed_at"] = datetime.now()
                if status == "skipped":
                    stop_dict["skip_reason"] = skip_reason
                updated_route.append(RouteStop(**stop_dict))
            else:
                updated_route.append(stop)

        # Save updated route (use mode='json' to serialize datetime objects)
        route_json = json.dumps([stop.model_dump(mode='json') for stop in updated_route])
        self.conn.execute(
            "UPDATE roll_calls SET route = ? WHERE id = ?",
            (route_json, rollcall_id),
        )
        self.conn.commit()

        return self.get_by_id(rollcall_id)

    def delete(self, rollcall_id: str) -> bool:
        """
        Delete roll call record.

        Args:
            rollcall_id: Roll call ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM roll_calls WHERE id = ?",
            (rollcall_id,),
        )
        self.conn.commit()

        return cursor.rowcount > 0

    def _row_to_rollcall(self, row: sqlite3.Row) -> RollCall:
        """
        Convert database row to RollCall model.

        Args:
            row: SQLite row

        Returns:
            RollCall model instance
        """
        # Deserialize route from JSON
        route_data = json.loads(row["route"])
        route = [RouteStop(**stop) for stop in route_data]

        return RollCall(
            id=row["id"],
            name=row["name"],
            status=RollCallStatus(row["status"]),
            scheduled_at=datetime.fromisoformat(row["scheduled_at"]),
            started_at=(
                datetime.fromisoformat(row["started_at"])
                if row["started_at"]
                else None
            ),
            completed_at=(
                datetime.fromisoformat(row["completed_at"])
                if row["completed_at"]
                else None
            ),
            cancelled_reason=row["cancelled_reason"],
            route=route,
            officer_id=row["officer_id"],
            notes=row["notes"] or "",
        )