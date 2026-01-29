"""
Schedule repository.

Handles database operations for schedule entries.
"""
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

from app.models.schedule import (
    ActivityType,
    ScheduleEntry,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
)


class ScheduleRepository:
    """Repository for schedule entry database operations."""

    def __init__(self, db: sqlite3.Connection):
        """Initialize repository with database connection."""
        self.db = db

    def create(self, entry: ScheduleEntryCreate, source: str = "manual") -> ScheduleEntry:
        """Create a new schedule entry."""
        entry_id = str(uuid.uuid4())
        now = datetime.utcnow().isoformat()

        self.db.execute(
            """
            INSERT INTO schedule_entries 
            (id, inmate_id, location_id, day_of_week, start_time, end_time, 
             activity_type, is_recurring, effective_date, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                entry.inmate_id,
                entry.location_id,
                entry.day_of_week,
                entry.start_time,
                entry.end_time,
                entry.activity_type.value,
                1 if entry.is_recurring else 0,
                entry.effective_date.isoformat() if entry.effective_date else None,
                source,
                now,
                now,
            ),
        )
        self.db.commit()

        return self.get_by_id(entry_id)

    def get_by_id(self, entry_id: str) -> Optional[ScheduleEntry]:
        """Get schedule entry by ID."""
        cursor = self.db.execute(
            """
            SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
                   activity_type, is_recurring, effective_date, source, source_id,
                   created_at, updated_at
            FROM schedule_entries
            WHERE id = ?
            """,
            (entry_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        return self._row_to_model(row)

    def get_by_inmate(self, inmate_id: str) -> list[ScheduleEntry]:
        """Get all schedule entries for an inmate."""
        cursor = self.db.execute(
            """
            SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
                   activity_type, is_recurring, effective_date, source, source_id,
                   created_at, updated_at
            FROM schedule_entries
            WHERE inmate_id = ?
            ORDER BY day_of_week, start_time
            """,
            (inmate_id,),
        )
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def get_by_location(self, location_id: str, day_of_week: Optional[int] = None) -> list[ScheduleEntry]:
        """Get all schedule entries for a location, optionally filtered by day."""
        if day_of_week is not None:
            cursor = self.db.execute(
                """
                SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
                       activity_type, is_recurring, effective_date, source, source_id,
                       created_at, updated_at
                FROM schedule_entries
                WHERE location_id = ? AND day_of_week = ?
                ORDER BY start_time
                """,
                (location_id, day_of_week),
            )
        else:
            cursor = self.db.execute(
                """
                SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
                       activity_type, is_recurring, effective_date, source, source_id,
                       created_at, updated_at
                FROM schedule_entries
                WHERE location_id = ?
                ORDER BY day_of_week, start_time
                """,
                (location_id,),
            )
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def get_at_time(
        self, day_of_week: int, time: str, location_id: Optional[str] = None
    ) -> list[ScheduleEntry]:
        """Get all schedule entries active at a specific day/time."""
        if location_id:
            cursor = self.db.execute(
                """
                SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
                       activity_type, is_recurring, effective_date, source, source_id,
                       created_at, updated_at
                FROM schedule_entries
                WHERE day_of_week = ? 
                  AND start_time <= ? 
                  AND end_time > ?
                  AND location_id = ?
                ORDER BY start_time
                """,
                (day_of_week, time, time, location_id),
            )
        else:
            cursor = self.db.execute(
                """
                SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
                       activity_type, is_recurring, effective_date, source, source_id,
                       created_at, updated_at
                FROM schedule_entries
                WHERE day_of_week = ? 
                  AND start_time <= ? 
                  AND end_time > ?
                ORDER BY start_time
                """,
                (day_of_week, time, time),
            )
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def update(self, entry_id: str, update: ScheduleEntryUpdate) -> Optional[ScheduleEntry]:
        """Update a schedule entry."""
        # Build dynamic update query
        updates = []
        params = []

        if update.location_id is not None:
            updates.append("location_id = ?")
            params.append(update.location_id)
        if update.start_time is not None:
            updates.append("start_time = ?")
            params.append(update.start_time)
        if update.end_time is not None:
            updates.append("end_time = ?")
            params.append(update.end_time)
        if update.activity_type is not None:
            updates.append("activity_type = ?")
            params.append(update.activity_type.value)

        if not updates:
            return self.get_by_id(entry_id)

        updates.append("updated_at = ?")
        params.append(datetime.utcnow().isoformat())
        params.append(entry_id)

        query = f"UPDATE schedule_entries SET {', '.join(updates)} WHERE id = ?"
        self.db.execute(query, params)
        self.db.commit()

        return self.get_by_id(entry_id)

    def delete(self, entry_id: str) -> bool:
        """Delete a schedule entry."""
        cursor = self.db.execute("DELETE FROM schedule_entries WHERE id = ?", (entry_id,))
        self.db.commit()
        return cursor.rowcount > 0

    def delete_by_source(self, source: str) -> int:
        """Delete all schedule entries from a specific source (for sync)."""
        cursor = self.db.execute("DELETE FROM schedule_entries WHERE source = ?", (source,))
        self.db.commit()
        return cursor.rowcount

    def list_all(self, limit: int = 100, offset: int = 0) -> list[ScheduleEntry]:
        """List all schedule entries with pagination."""
        cursor = self.db.execute(
            """
            SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
                   activity_type, is_recurring, effective_date, source, source_id,
                   created_at, updated_at
            FROM schedule_entries
            ORDER BY day_of_week, start_time
            LIMIT ? OFFSET ?
            """,
            (limit, offset),
        )
        return [self._row_to_model(row) for row in cursor.fetchall()]

    def count(self) -> int:
        """Count total schedule entries."""
        cursor = self.db.execute("SELECT COUNT(*) FROM schedule_entries")
        return cursor.fetchone()[0]

    def _row_to_model(self, row: tuple) -> ScheduleEntry:
        """Convert database row to ScheduleEntry model."""
        return ScheduleEntry(
            id=row[0],
            inmate_id=row[1],
            location_id=row[2],
            day_of_week=row[3],
            start_time=row[4],
            end_time=row[5],
            activity_type=ActivityType(row[6]),
            is_recurring=bool(row[7]),
            effective_date=row[8],
            source=row[9],
            source_id=row[10],
            created_at=datetime.fromisoformat(row[11]),
            updated_at=datetime.fromisoformat(row[12]),
        )
