"""
Test suite for EmbeddingRepository.

Tests storage and retrieval of face embeddings.
"""
import numpy as np
import pytest

from app.db.database import get_connection, init_db
from app.db.repositories.embedding_repo import EmbeddingRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.models.inmate import InmateCreate


@pytest.fixture
def db_conn():
    """Create an in-memory database connection for testing."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def embedding_repo(db_conn):
    """Create an EmbeddingRepository instance."""
    return EmbeddingRepository(db_conn)


@pytest.fixture
def inmate_repo(db_conn):
    """Create an InmateRepository instance."""
    return InmateRepository(db_conn)


@pytest.fixture
def sample_embedding():
    """Create a sample 512-dimensional embedding."""
    return np.random.rand(512).astype(np.float32)


@pytest.fixture
def sample_inmate(inmate_repo):
    """Create a sample inmate."""
    from datetime import date

    return inmate_repo.create(
        InmateCreate(
            inmate_number="A12345",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
        )
    )


class TestEmbeddingRepositorySave:
    """Test saving embeddings."""

    def test_save_embedding_success(
        self, embedding_repo, sample_inmate, sample_embedding
    ):
        """Should save embedding for inmate."""
        embedding_repo.save(
            sample_inmate.id,
            sample_embedding,
            model_version="arcface_r100",
        )

        # Verify saved
        retrieved = embedding_repo.get(sample_inmate.id)
        assert retrieved is not None
        assert np.allclose(retrieved, sample_embedding)

    def test_save_embedding_replace(
        self, embedding_repo, sample_inmate, sample_embedding
    ):
        """Should replace existing embedding."""
        # Save first embedding
        embedding_repo.save(sample_inmate.id, sample_embedding, "v1")

        # Save second embedding (should replace)
        new_embedding = np.random.rand(512).astype(np.float32)
        embedding_repo.save(sample_inmate.id, new_embedding, "v2")

        # Verify new embedding
        retrieved = embedding_repo.get(sample_inmate.id)
        assert np.allclose(retrieved, new_embedding)
        assert not np.allclose(retrieved, sample_embedding)

    def test_save_embedding_correct_shape(
        self, embedding_repo, sample_inmate, sample_embedding
    ):
        """Should save and retrieve embedding with correct shape."""
        embedding_repo.save(sample_inmate.id, sample_embedding, "v1")

        retrieved = embedding_repo.get(sample_inmate.id)
        assert retrieved.shape == (512,)
        assert retrieved.dtype == np.float32


class TestEmbeddingRepositoryGet:
    """Test retrieving embeddings."""

    def test_get_embedding_found(
        self, embedding_repo, sample_inmate, sample_embedding
    ):
        """Should retrieve saved embedding."""
        embedding_repo.save(sample_inmate.id, sample_embedding, "v1")

        retrieved = embedding_repo.get(sample_inmate.id)
        assert retrieved is not None
        assert np.allclose(retrieved, sample_embedding)

    def test_get_embedding_not_found(self, embedding_repo):
        """Should return None for non-existent embedding."""
        result = embedding_repo.get("non-existent-id")
        assert result is None

    def test_get_all_empty(self, embedding_repo):
        """Should return empty dict when no embeddings exist."""
        embeddings = embedding_repo.get_all()
        assert embeddings == {}

    def test_get_all_multiple(self, embedding_repo, inmate_repo):
        """Should retrieve all embeddings."""
        from datetime import date

        # Create multiple inmates
        inmate1 = inmate_repo.create(
            InmateCreate(
                inmate_number="A001",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 1),
                cell_block="A",
                cell_number="101",
            )
        )
        inmate2 = inmate_repo.create(
            InmateCreate(
                inmate_number="A002",
                first_name="Jane",
                last_name="Smith",
                date_of_birth=date(1991, 2, 2),
                cell_block="A",
                cell_number="102",
            )
        )

        # Save embeddings
        emb1 = np.random.rand(512).astype(np.float32)
        emb2 = np.random.rand(512).astype(np.float32)
        embedding_repo.save(inmate1.id, emb1, "v1")
        embedding_repo.save(inmate2.id, emb2, "v1")

        # Get all
        embeddings = embedding_repo.get_all()
        assert len(embeddings) == 2
        assert inmate1.id in embeddings
        assert inmate2.id in embeddings
        assert np.allclose(embeddings[inmate1.id], emb1)
        assert np.allclose(embeddings[inmate2.id], emb2)


class TestEmbeddingRepositoryDelete:
    """Test deleting embeddings."""

    def test_delete_success(self, embedding_repo, sample_inmate, sample_embedding):
        """Should delete embedding."""
        embedding_repo.save(sample_inmate.id, sample_embedding, "v1")

        result = embedding_repo.delete(sample_inmate.id)
        assert result is True
        assert embedding_repo.get(sample_inmate.id) is None

    def test_delete_not_found(self, embedding_repo):
        """Should return False when deleting non-existent embedding."""
        result = embedding_repo.delete("non-existent-id")
        assert result is False


class TestEmbeddingRepositoryModelVersion:
    """Test model version tracking."""

    def test_get_model_version(
        self, embedding_repo, sample_inmate, sample_embedding
    ):
        """Should retrieve model version."""
        embedding_repo.save(sample_inmate.id, sample_embedding, "arcface_r100")

        version = embedding_repo.get_model_version(sample_inmate.id)
        assert version == "arcface_r100"

    def test_get_model_version_not_found(self, embedding_repo):
        """Should return None for non-existent embedding."""
        version = embedding_repo.get_model_version("non-existent-id")
        assert version is None


class TestEmbeddingRepositoryBinaryConversion:
    """Test binary conversion integrity."""

    def test_embedding_roundtrip(
        self, embedding_repo, sample_inmate, sample_embedding
    ):
        """Should maintain embedding precision after save/load."""
        embedding_repo.save(sample_inmate.id, sample_embedding, "v1")
        retrieved = embedding_repo.get(sample_inmate.id)

        # Check exact equality (within floating point precision)
        assert np.allclose(retrieved, sample_embedding, rtol=1e-6, atol=1e-8)

    def test_embedding_values_preserved(
        self, embedding_repo, sample_inmate
    ):
        """Should preserve specific embedding values."""
        # Create embedding with known values
        embedding = np.array([0.1, 0.5, 0.9, -0.3] + [0.0] * 508, dtype=np.float32)

        embedding_repo.save(sample_inmate.id, embedding, "v1")
        retrieved = embedding_repo.get(sample_inmate.id)

        assert retrieved[0] == pytest.approx(0.1)
        assert retrieved[1] == pytest.approx(0.5)
        assert retrieved[2] == pytest.approx(0.9)
        assert retrieved[3] == pytest.approx(-0.3)
