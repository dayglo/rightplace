"""
Embedding repository for database operations.

Handles storage and retrieval of face embeddings.
"""
import sqlite3
from datetime import datetime
from typing import Optional

import numpy as np


class EmbeddingRepository:
    """Repository for face embedding database operations."""

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
        """
        self.conn = conn

    def save(
        self,
        inmate_id: str,
        embedding: np.ndarray,
        model_version: str,
    ) -> None:
        """
        Save face embedding for an inmate.

        Uses INSERT OR REPLACE to update existing embeddings.

        Args:
            inmate_id: Inmate ID
            embedding: 512-dimensional face embedding
            model_version: ML model version used
        """
        # Convert NumPy array to bytes
        blob = embedding.astype(np.float32).tobytes()

        self.conn.execute(
            """
            INSERT OR REPLACE INTO embeddings (inmate_id, embedding, model_version, created_at)
            VALUES (?, ?, ?, ?)
            """,
            (inmate_id, blob, model_version, datetime.now().isoformat()),
        )
        self.conn.commit()

    def get(self, inmate_id: str) -> Optional[np.ndarray]:
        """
        Retrieve face embedding for an inmate.

        Args:
            inmate_id: Inmate ID

        Returns:
            512-dimensional embedding if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT embedding FROM embeddings WHERE inmate_id = ?",
            (inmate_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        # Convert bytes back to NumPy array
        return np.frombuffer(row[0], dtype=np.float32)

    def get_all(self) -> dict[str, np.ndarray]:
        """
        Retrieve all embeddings.

        Returns:
            Dictionary mapping inmate_id to embedding
        """
        cursor = self.conn.execute("SELECT inmate_id, embedding FROM embeddings")
        rows = cursor.fetchall()

        return {
            row[0]: np.frombuffer(row[1], dtype=np.float32) for row in rows
        }

    def delete(self, inmate_id: str) -> bool:
        """
        Delete embedding for an inmate.

        Args:
            inmate_id: Inmate ID

        Returns:
            True if deleted, False if not found
        """
        cursor = self.conn.execute(
            "DELETE FROM embeddings WHERE inmate_id = ?",
            (inmate_id,),
        )
        self.conn.commit()

        return cursor.rowcount > 0

    def get_model_version(self, inmate_id: str) -> Optional[str]:
        """
        Get the model version used for an embedding.

        Args:
            inmate_id: Inmate ID

        Returns:
            Model version if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT model_version FROM embeddings WHERE inmate_id = ?",
            (inmate_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return row[0]
