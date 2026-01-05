"""
Inmate repository for database operations.

Handles CRUD operations for inmate records.
"""
import sqlite3
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.inmate import Inmate, InmateCreate, InmateUpdate


class InmateRepository:
    """Repository for inmate database operations."""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def create(self, inmate_data: InmateCreate) -> Inmate:
        """
        Create a new inmate record.

        Args:
            inmate_data: Inmate creation data

        Returns:
            Created inmate with generated ID and timestamps
        """
        inmate_id = str(uuid4())
        now = datetime.now()

        self.conn.execute(
            """
            INSERT INTO inmates (
                id, inmate_number, first_name, last_name,
                date_of_birth, cell_block, cell_number,
                is_enrolled, is_active, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                inmate_id,
                inmate_data.inmate_number,
                inmate_data.first_name,
                inmate_data.last_name,
                inmate_data.date_of_birth.isoformat(),
                inmate_data.cell_block,
                inmate_data.cell_number,
                0,  # is_enrolled defaults to False
                1,  # is_active defaults to True
                now.isoformat(),
                now.isoformat(),
            ),
        )
        self.conn.commit()

        return self.get_by_id(inmate_id)  # type: ignore

    def get_by_id(self, inmate_id: str) -> Optional[Inmate]:
        """
        Retrieve inmate by ID.

        Args:
            inmate_id: Inmate ID

        Returns:
            Inmate if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM inmates WHERE id = ?",
            (inmate_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_inmate(row)

    def get_by_inmate_number(self, inmate_number: str) -> Optional[Inmate]:
        """
        Retrieve inmate by inmate number.

        Args:
            inmate_number: Facility inmate number

        Returns:
            Inmate if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM inmates WHERE inmate_number = ?",
            (inmate_number,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_inmate(row)

    def get_all(self) -> list[Inmate]:
        """
        Retrieve all inmates.

        Returns:
            List of all inmates
        """
        cursor = self.conn.execute("SELECT * FROM inmates ORDER BY created_at")
        rows = cursor.fetchall()

        return [self._row_to_inmate(row) for row in rows]

    def get_by_block(self, cell_block: str) -> list[Inmate]:
        """
        Retrieve inmates by cell block.

        Args:
            cell_block: Cell block identifier

        Returns:
            List of inmates in the specified block
        """
        cursor = self.conn.execute(
            "SELECT * FROM inmates WHERE cell_block = ? ORDER BY cell_number",
            (cell_block,),
        )
        rows = cursor.fetchall()

        return [self._row_to_inmate(row) for row in rows]

    def get_enrolled(self) -> list[Inmate]:
        """
        Retrieve all enrolled inmates.

        Returns:
            List of enrolled inmates
        """
        cursor = self.conn.execute(
            "SELECT * FROM inmates WHERE is_enrolled = 1 ORDER BY created_at"
        )
        rows = cursor.fetchall()

        return [self._row_to_inmate(row) for row in rows]

    def update(
        self,
        inmate_id: str,
        update_data: InmateUpdate,
        is_enrolled: Optional[bool] = None,
        enrolled_at: Optional[datetime] = None,
    ) -> Optional[Inmate]:
        """
        Update inmate record.

        Args:
            inmate_id: Inmate ID
            update_data: Fields to update
            is_enrolled: Optional enrollment status
            enrolled_at: Optional enrollment timestamp

        Returns:
            Updated inmate if found, None otherwise
        """
        # Check if inmate exists
        existing = self.get_by_id(inmate_id)
        if existing is None:
            return None

        # Build update query dynamically
        updates = []
        params = []

        if update_data.first_name is not None:
            updates.append("first_name = ?")
            params.append(update_data.first_name)

        if update_data.last_name is not None:
            updates.append("last_name = ?")
            params.append(update_data.last_name)

        if update_data.cell_block is not None:
            updates.append("cell_block = ?")
            params.append(update_data.cell_block)

        if update_data.cell_number is not None:
            updates.append("cell_number = ?")
            params.append(update_data.cell_number)

        if update_data.is_active is not None:
            updates.append("is_active = ?")
            params.append(1 if update_data.is_active else 0)

        if is_enrolled is not None:
            updates.append("is_enrolled = ?")
            params.append(1 if is_enrolled else 0)

        if enrolled_at is not None:
            updates.append("enrolled_at = ?")
            params.append(enrolled_at.isoformat())

        # Always update updated_at
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())

        # Add inmate_id for WHERE clause
        params.append(inmate_id)

        # Execute update
        query = f"UPDATE inmates SET {', '.join(updates)} WHERE id = ?"
        self.conn.execute(query, params)
        self.conn.commit()

        return self.get_by_id(inmate_id)

    def delete(self, inmate_id: str) -> bool:
        """
        Delete inmate record.

        Args:
            inmate_id: Inmate ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM inmates WHERE id = ?",
            (inmate_id,),
        )
        self.conn.commit()

        return cursor.rowcount > 0

    def _row_to_inmate(self, row: sqlite3.Row) -> Inmate:
        """
        Convert database row to Inmate model.

        Args:
            row: SQLite row

        Returns:
            Inmate model instance
        """
        return Inmate(
            id=row["id"],
            inmate_number=row["inmate_number"],
            first_name=row["first_name"],
            last_name=row["last_name"],
            date_of_birth=datetime.fromisoformat(row["date_of_birth"]).date(),
            cell_block=row["cell_block"],
            cell_number=row["cell_number"],
            photo_uri=row["photo_uri"],
            is_enrolled=bool(row["is_enrolled"]),
            enrolled_at=(
                datetime.fromisoformat(row["enrolled_at"])
                if row["enrolled_at"]
                else None
            ),
            is_active=bool(row["is_active"]),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
        )
