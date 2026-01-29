"""
Location repository for database operations.

Handles CRUD operations for location records.
"""
import sqlite3
from typing import Optional
from uuid import uuid4

from app.models.location import Location, LocationType, LocationCreate, LocationUpdate


class LocationRepository:
    """Repository for location database operations."""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def create(self, location_data: LocationCreate) -> Location:
        """
        Create a new location record.

        Args:
            location_data: Location creation data

        Returns:
            Created location with generated ID
        """
        location_id = str(uuid4())

        self.conn.execute(
            """
            INSERT INTO locations (
                id, name, type, parent_id, capacity, floor, building
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                location_id,
                location_data.name,
                location_data.type.value,
                location_data.parent_id,
                location_data.capacity,
                location_data.floor,
                location_data.building,
            ),
        )
        self.conn.commit()

        return self.get_by_id(location_id)  # type: ignore

    def get_by_id(self, location_id: str) -> Optional[Location]:
        """
        Retrieve location by ID.

        Args:
            location_id: Location ID

        Returns:
            Location if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM locations WHERE id = ?",
            (location_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_location(row)

    def get_all(self) -> list[Location]:
        """
        Retrieve all locations.

        Returns:
            List of all locations
        """
        cursor = self.conn.execute("SELECT * FROM locations ORDER BY name")
        rows = cursor.fetchall()

        return [self._row_to_location(row) for row in rows]

    def get_by_type(self, location_type: LocationType) -> list[Location]:
        """
        Retrieve locations by type.

        Args:
            location_type: Location type

        Returns:
            List of locations of the specified type
        """
        cursor = self.conn.execute(
            "SELECT * FROM locations WHERE type = ? ORDER BY name",
            (location_type.value,),
        )
        rows = cursor.fetchall()

        return [self._row_to_location(row) for row in rows]

    def get_by_building(self, building: str) -> list[Location]:
        """
        Retrieve locations by building.

        Args:
            building: Building identifier

        Returns:
            List of locations in the specified building
        """
        cursor = self.conn.execute(
            "SELECT * FROM locations WHERE building = ? ORDER BY name",
            (building,),
        )
        rows = cursor.fetchall()

        return [self._row_to_location(row) for row in rows]

    def get_children(self, parent_id: str) -> list[Location]:
        """
        Retrieve child locations of a parent location.

        Args:
            parent_id: Parent location ID

        Returns:
            List of child locations
        """
        cursor = self.conn.execute(
            "SELECT * FROM locations WHERE parent_id = ? ORDER BY name",
            (parent_id,),
        )
        rows = cursor.fetchall()

        return [self._row_to_location(row) for row in rows]

    def get_all_descendants(
        self, parent_id: str, type_filter: Optional[LocationType] = None
    ) -> list[Location]:
        """
        Retrieve all descendant locations recursively.

        Uses recursive CTE to get full tree under a parent location.

        Args:
            parent_id: Parent location ID
            type_filter: Optional filter to only return locations of this type

        Returns:
            List of all descendant locations
        """
        # SQLite recursive CTE to get all descendants
        cursor = self.conn.execute(
            """
            WITH RECURSIVE location_tree AS (
                -- Base case: direct children
                SELECT id, name, type, parent_id, capacity, floor, building, 1 as depth
                FROM locations
                WHERE parent_id = ?
                
                UNION ALL
                
                -- Recursive case: children of children
                SELECT l.id, l.name, l.type, l.parent_id, l.capacity, l.floor, l.building, lt.depth + 1
                FROM locations l
                JOIN location_tree lt ON l.parent_id = lt.id
            )
            SELECT id, name, type, parent_id, capacity, floor, building
            FROM location_tree
            ORDER BY depth, name
            """,
            (parent_id,),
        )
        rows = cursor.fetchall()
        
        locations = [self._row_to_location(row) for row in rows]
        
        # Apply type filter if specified
        if type_filter:
            locations = [loc for loc in locations if loc.type == type_filter]
        
        return locations

    def update(
        self, location_id: str, location_data: LocationUpdate
    ) -> Optional[Location]:
        """
        Update location record.

        Args:
            location_id: Location ID
            location_data: Location update data

        Returns:
            Updated location if found, None otherwise
        """
        # Check if location exists
        existing = self.get_by_id(location_id)
        if existing is None:
            return None

        # Build update query dynamically
        updates = []
        params = []

        if location_data.name is not None:
            updates.append("name = ?")
            params.append(location_data.name)

        if location_data.type is not None:
            updates.append("type = ?")
            params.append(location_data.type.value)

        if location_data.building is not None:
            updates.append("building = ?")
            params.append(location_data.building)

        if location_data.parent_id is not None:
            updates.append("parent_id = ?")
            params.append(location_data.parent_id)

        if location_data.capacity is not None:
            updates.append("capacity = ?")
            params.append(location_data.capacity)

        if location_data.floor is not None:
            updates.append("floor = ?")
            params.append(location_data.floor)

        # If no updates, return existing
        if not updates:
            return existing

        # Add location_id for WHERE clause
        params.append(location_id)

        # Execute update
        query = f"UPDATE locations SET {', '.join(updates)} WHERE id = ?"
        self.conn.execute(query, params)
        self.conn.commit()

        return self.get_by_id(location_id)

    def delete(self, location_id: str) -> bool:
        """
        Delete location record.

        Args:
            location_id: Location ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM locations WHERE id = ?",
            (location_id,),
        )
        self.conn.commit()

        return cursor.rowcount > 0

    def _row_to_location(self, row: sqlite3.Row) -> Location:
        """
        Convert database row to Location model.

        Args:
            row: SQLite row

        Returns:
            Location model instance
        """
        return Location(
            id=row["id"],
            name=row["name"],
            type=LocationType(row["type"]),
            parent_id=row["parent_id"],
            capacity=row["capacity"],
            floor=row["floor"],
            building=row["building"],
        )
