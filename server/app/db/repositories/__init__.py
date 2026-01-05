"""
Database repositories package.

Exports all repository classes for data access.
"""
from app.db.repositories.embedding_repo import EmbeddingRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository

__all__ = [
    "InmateRepository",
    "LocationRepository",
    "EmbeddingRepository",
]
