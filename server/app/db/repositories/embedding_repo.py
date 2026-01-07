"""
Embedding repository for database operations.

Handles storage and retrieval of face embeddings.
"""
import sqlite3
import uuid
from datetime import datetime
from typing import Optional

import numpy as np


class EmbeddingRepository:
    """Repository for face embedding database operations."""

    def __init__(self, conn: sqlite3.Connection, max_embeddings_per_inmate: int = 5):
        """
        Initialize repository with database connection.

        Args:
            conn: SQLite database connection
            max_embeddings_per_inmate: Maximum number of embeddings to keep per inmate
        """
        self.conn = conn
        self.max_embeddings_per_inmate = max_embeddings_per_inmate

    def save(
        self,
        inmate_id: str,
        embedding: np.ndarray,
        model_version: str,
        quality: float = 1.0,
        photo_path: str | None = None,
    ) -> None:
        """
        Save face embedding for an inmate.

        Adds a new embedding and keeps only the N most recent embeddings.

        Args:
            inmate_id: Inmate ID
            embedding: 512-dimensional face embedding
            model_version: ML model version used
            quality: Quality score for this embedding (default: 1.0)
            photo_path: Optional path to enrollment photo
        """
        # Convert NumPy array to bytes
        blob = embedding.astype(np.float32).tobytes()
        
        # Generate unique ID
        embedding_id = str(uuid.uuid4())

        # Insert new embedding
        self.conn.execute(
            """
            INSERT INTO embeddings (id, inmate_id, embedding, photo_path, quality, model_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (embedding_id, inmate_id, blob, photo_path, quality, model_version, datetime.now().isoformat()),
        )
        
        # Keep only N most recent embeddings per inmate
        self.conn.execute(
            """
            DELETE FROM embeddings 
            WHERE inmate_id = ? 
            AND id NOT IN (
                SELECT id FROM embeddings 
                WHERE inmate_id = ? 
                ORDER BY created_at DESC 
                LIMIT ?
            )
            """,
            (inmate_id, inmate_id, self.max_embeddings_per_inmate),
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
        Retrieve all embeddings, averaged per inmate.

        DEPRECATED: Use get_all_with_quality() for ensemble matching.

        When multiple embeddings exist for an inmate, they are averaged
        into a single embedding for matching.

        Returns:
            Dictionary mapping inmate_id to averaged embedding
        """
        cursor = self.conn.execute("SELECT inmate_id, embedding FROM embeddings ORDER BY inmate_id")
        rows = cursor.fetchall()

        # Group embeddings by inmate_id
        inmate_embeddings: dict[str, list[np.ndarray]] = {}
        for row in rows:
            inmate_id = row[0]
            embedding = np.frombuffer(row[1], dtype=np.float32)
            
            if inmate_id not in inmate_embeddings:
                inmate_embeddings[inmate_id] = []
            inmate_embeddings[inmate_id].append(embedding)
        
        # Average embeddings for each inmate
        averaged = {}
        for inmate_id, embeddings in inmate_embeddings.items():
            if len(embeddings) == 1:
                averaged[inmate_id] = embeddings[0]
            else:
                # Average multiple embeddings
                avg_embedding = np.mean(embeddings, axis=0)
                # Re-normalize after averaging
                norm = np.linalg.norm(avg_embedding)
                if norm > 0:
                    avg_embedding = avg_embedding / norm
                averaged[inmate_id] = avg_embedding
        
        return averaged
    
    def get_all_with_quality(self) -> dict[str, list[dict[str, any]]]:
        """
        Retrieve all embeddings with quality scores per inmate.
        
        Returns individual embeddings (not averaged) with their quality scores
        for ensemble matching strategies.

        Returns:
            Dictionary mapping inmate_id to list of embedding dicts:
            {
                "inmate_id": [
                    {"embedding": np.ndarray, "quality": float, "photo_path": str},
                    ...
                ]
            }
        """
        cursor = self.conn.execute(
            "SELECT inmate_id, embedding, quality, photo_path FROM embeddings ORDER BY inmate_id"
        )
        rows = cursor.fetchall()

        # Group embeddings by inmate_id with quality scores
        inmate_data: dict[str, list[dict]] = {}
        for row in rows:
            inmate_id = row[0]
            embedding = np.frombuffer(row[1], dtype=np.float32)
            quality = row[2]
            photo_path = row[3]
            
            if inmate_id not in inmate_data:
                inmate_data[inmate_id] = []
            
            inmate_data[inmate_id].append({
                "embedding": embedding,
                "quality": quality,
                "photo_path": photo_path
            })
        
        return inmate_data

    def get_count(self, inmate_id: str) -> int:
        """
        Get the number of embeddings for an inmate.

        Args:
            inmate_id: Inmate ID

        Returns:
            Number of embeddings stored for this inmate
        """
        cursor = self.conn.execute(
            "SELECT COUNT(*) FROM embeddings WHERE inmate_id = ?",
            (inmate_id,),
        )
        row = cursor.fetchone()
        return row[0] if row else 0

    def get_photo_paths(self, inmate_id: str) -> list[dict[str, any]]:
        """
        Get enrollment photo paths and quality scores for an inmate.

        Args:
            inmate_id: Inmate ID

        Returns:
            List of dicts with photo_path and quality for each enrollment
        """
        cursor = self.conn.execute(
            """
            SELECT photo_path, quality, created_at 
            FROM embeddings 
            WHERE inmate_id = ? 
            ORDER BY created_at ASC
            """,
            (inmate_id,),
        )
        rows = cursor.fetchall()
        
        return [
            {
                "photo_path": row[0],
                "quality": row[1],
                "created_at": row[2],
            }
            for row in rows if row[0]  # Only include if photo_path exists
        ]

    def delete(self, inmate_id: str) -> bool:
        """
        Delete all embeddings for an inmate.

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
        Get the model version used for embeddings.

        Args:
            inmate_id: Inmate ID

        Returns:
            Model version if found, None otherwise
        """
        cursor = self.conn.execute(
            "SELECT model_version FROM embeddings WHERE inmate_id = ? LIMIT 1",
            (inmate_id,),
        )
        row = cursor.fetchone()

        if row is None:
            return None

        return row[0]
