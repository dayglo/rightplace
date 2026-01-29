"""
Connection repository for database operations.

Handles CRUD operations for location connection records.
"""
import sqlite3
from datetime import datetime
from typing import Optional
from uuid import uuid4

from app.models.location import LocationConnection, LocationConnectionCreate


class ConnectionRepository:
    """Repository for location connection database operations."""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def create(self, connection_data: LocationConnectionCreate) -> LocationConnection:
        """
        Create a new location connection record.

        Args:
            connection_data: Connection creation data

        Returns:
            Created connection with generated ID and timestamps
        """
        connection_id = str(uuid4())
        now = datetime.utcnow().isoformat()

        self.conn.execute(
            """
            INSERT INTO location_connections (
                id, from_location_id, to_location_id, distance_meters,
                travel_time_seconds, connection_type, is_bidirectional,
                requires_escort, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                connection_id,
                connection_data.from_location_id,
                connection_data.to_location_id,
                connection_data.distance_meters,
                connection_data.travel_time_seconds,
                connection_data.connection_type,
                1 if connection_data.is_bidirectional else 0,
                1 if connection_data.requires_escort else 0,
                now,
                now,
            ),
        )
        self.conn.commit()

        return self.get_by_id(connection_id)  # type: ignore

    def get_by_id(self, connection_id: str) -> Optional[LocationConnection]:
        """
        Retrieve connection by ID.

        Args:
            connection_id: Connection ID

        Returns:
            LocationConnection if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT * FROM location_connections WHERE id = ?",
            (connection_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return self._row_to_connection(row)

    def get_all(self) -> list[LocationConnection]:
        """
        Retrieve all location connections.

        Returns:
            List of all connections
        """
        cursor = self.conn.execute(
            "SELECT * FROM location_connections ORDER BY from_location_id"
        )
        rows = cursor.fetchall()

        return [self._row_to_connection(row) for row in rows]

    def get_from_location(self, location_id: str) -> list[LocationConnection]:
        """
        Retrieve all connections from a specific location.

        Args:
            location_id: Source location ID

        Returns:
            List of connections originating from the location
        """
        cursor = self.conn.execute(
            """
            SELECT * FROM location_connections 
            WHERE from_location_id = ?
            ORDER BY to_location_id
            """,
            (location_id,),
        )
        rows = cursor.fetchall()

        return [self._row_to_connection(row) for row in rows]

    def get_graph(self) -> dict[str, list[tuple[str, int]]]:
        """
        Build adjacency list graph representation.

        Returns:
            Dictionary mapping location_id to list of (neighbor_id, travel_time) tuples
        """
        graph: dict[str, list[tuple[str, int]]] = {}
        
        connections = self.get_all()
        
        for conn in connections:
            # Add forward edge
            if conn.from_location_id not in graph:
                graph[conn.from_location_id] = []
            graph[conn.from_location_id].append(
                (conn.to_location_id, conn.travel_time_seconds)
            )
            
            # Add backward edge if bidirectional
            if conn.is_bidirectional:
                if conn.to_location_id not in graph:
                    graph[conn.to_location_id] = []
                graph[conn.to_location_id].append(
                    (conn.from_location_id, conn.travel_time_seconds)
                )
        
        return graph

    def delete(self, connection_id: str) -> bool:
        """
        Delete connection record.

        Args:
            connection_id: Connection ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM location_connections WHERE id = ?",
            (connection_id,),
        )
        self.conn.commit()

        return cursor.rowcount > 0

    def _row_to_connection(self, row: sqlite3.Row) -> LocationConnection:
        """
        Convert database row to LocationConnection model.

        Args:
            row: SQLite row

        Returns:
            LocationConnection model instance
        """
        return LocationConnection(
            id=row["id"],
            from_location_id=row["from_location_id"],
            to_location_id=row["to_location_id"],
            distance_meters=row["distance_meters"],
            travel_time_seconds=row["travel_time_seconds"],
            connection_type=row["connection_type"],
            is_bidirectional=bool(row["is_bidirectional"]),
            requires_escort=bool(row["requires_escort"]),
        )
