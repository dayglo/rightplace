"""
Test suite for InmateRepository.

Tests CRUD operations and queries for inmate data.
"""
from datetime import date, datetime
from uuid import uuid4

import pytest

from app.db.database import get_connection, init_db
from app.db.repositories.inmate_repo import InmateRepository
from app.models.inmate import Inmate, InmateCreate, InmateUpdate


@pytest.fixture
def db_conn():
    """Create an in-memory database connection for testing."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def inmate_repo(db_conn):
    """Create an InmateRepository instance."""
    return InmateRepository(db_conn)


@pytest.fixture
def sample_inmate_data():
    """Sample inmate data for testing."""
    return InmateCreate(
        inmate_number="A12345",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 1),
        cell_block="A",
        cell_number="101",
    )


class TestInmateRepositoryCreate:
    """Test inmate creation."""

    def test_create_inmate_success(self, inmate_repo, sample_inmate_data):
        """Should create inmate with all required fields."""
        inmate = inmate_repo.create(sample_inmate_data)

        assert inmate.id is not None
        assert inmate.inmate_number == "A12345"
        assert inmate.first_name == "John"
        assert inmate.last_name == "Doe"
        assert inmate.date_of_birth == date(1990, 1, 1)
        assert inmate.cell_block == "A"
        assert inmate.cell_number == "101"
        assert inmate.is_enrolled is False
        assert inmate.is_active is True
        assert inmate.created_at is not None
        assert inmate.updated_at is not None

    def test_create_multiple_inmates(self, inmate_repo):
        """Should create multiple inmates with unique IDs."""
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

        assert inmate1.id != inmate2.id
        assert inmate1.inmate_number != inmate2.inmate_number


class TestInmateRepositoryRead:
    """Test reading inmate records."""

    def test_get_by_id_found(self, inmate_repo, sample_inmate_data):
        """Should retrieve inmate by ID."""
        created = inmate_repo.create(sample_inmate_data)
        retrieved = inmate_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.inmate_number == created.inmate_number

    def test_get_by_id_not_found(self, inmate_repo):
        """Should return None for non-existent ID."""
        result = inmate_repo.get_by_id("non-existent-id")
        assert result is None

    def test_get_by_inmate_number_found(self, inmate_repo, sample_inmate_data):
        """Should retrieve inmate by inmate number."""
        created = inmate_repo.create(sample_inmate_data)
        retrieved = inmate_repo.get_by_inmate_number("A12345")

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.inmate_number == "A12345"

    def test_get_by_inmate_number_not_found(self, inmate_repo):
        """Should return None for non-existent inmate number."""
        result = inmate_repo.get_by_inmate_number("Z99999")
        assert result is None

    def test_get_all_empty(self, inmate_repo):
        """Should return empty list when no inmates exist."""
        inmates = inmate_repo.get_all()
        assert inmates == []

    def test_get_all_multiple(self, inmate_repo):
        """Should return all inmates."""
        inmate_repo.create(
            InmateCreate(
                inmate_number="A001",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 1),
                cell_block="A",
                cell_number="101",
            )
        )
        inmate_repo.create(
            InmateCreate(
                inmate_number="A002",
                first_name="Jane",
                last_name="Smith",
                date_of_birth=date(1991, 2, 2),
                cell_block="B",
                cell_number="201",
            )
        )

        inmates = inmate_repo.get_all()
        assert len(inmates) == 2

    def test_get_by_block(self, inmate_repo):
        """Should retrieve inmates by cell block."""
        inmate_repo.create(
            InmateCreate(
                inmate_number="A001",
                first_name="John",
                last_name="Doe",
                date_of_birth=date(1990, 1, 1),
                cell_block="A",
                cell_number="101",
            )
        )
        inmate_repo.create(
            InmateCreate(
                inmate_number="A002",
                first_name="Jane",
                last_name="Smith",
                date_of_birth=date(1991, 2, 2),
                cell_block="A",
                cell_number="102",
            )
        )
        inmate_repo.create(
            InmateCreate(
                inmate_number="B001",
                first_name="Bob",
                last_name="Johnson",
                date_of_birth=date(1992, 3, 3),
                cell_block="B",
                cell_number="201",
            )
        )

        block_a_inmates = inmate_repo.get_by_block("A")
        assert len(block_a_inmates) == 2
        assert all(inmate.cell_block == "A" for inmate in block_a_inmates)

    def test_get_enrolled(self, inmate_repo, sample_inmate_data):
        """Should retrieve only enrolled inmates."""
        # Create enrolled inmate
        created = inmate_repo.create(sample_inmate_data)
        inmate_repo.update(
            created.id,
            InmateUpdate(),
            is_enrolled=True,
            enrolled_at=datetime.now(),
        )

        # Create non-enrolled inmate
        inmate_repo.create(
            InmateCreate(
                inmate_number="A999",
                first_name="Jane",
                last_name="Smith",
                date_of_birth=date(1991, 2, 2),
                cell_block="B",
                cell_number="201",
            )
        )

        enrolled = inmate_repo.get_enrolled()
        assert len(enrolled) == 1
        assert enrolled[0].is_enrolled is True


class TestInmateRepositoryUpdate:
    """Test updating inmate records."""

    def test_update_success(self, inmate_repo, sample_inmate_data):
        """Should update inmate fields."""
        created = inmate_repo.create(sample_inmate_data)

        update_data = InmateUpdate(
            first_name="Jane",
            cell_block="B",
            cell_number="202",
        )

        updated = inmate_repo.update(created.id, update_data)

        assert updated is not None
        assert updated.id == created.id
        assert updated.first_name == "Jane"
        assert updated.last_name == "Doe"  # Unchanged
        assert updated.cell_block == "B"
        assert updated.cell_number == "202"
        assert updated.updated_at > created.updated_at

    def test_update_partial(self, inmate_repo, sample_inmate_data):
        """Should update only specified fields."""
        created = inmate_repo.create(sample_inmate_data)

        update_data = InmateUpdate(first_name="Jane")
        updated = inmate_repo.update(created.id, update_data)

        assert updated.first_name == "Jane"
        assert updated.last_name == "Doe"  # Unchanged
        assert updated.cell_block == "A"  # Unchanged

    def test_update_not_found(self, inmate_repo):
        """Should return None when updating non-existent inmate."""
        result = inmate_repo.update(
            "non-existent-id",
            InmateUpdate(first_name="Jane"),
        )
        assert result is None

    def test_update_enrollment(self, inmate_repo, sample_inmate_data):
        """Should update enrollment status."""
        created = inmate_repo.create(sample_inmate_data)
        enrolled_at = datetime.now()

        updated = inmate_repo.update(
            created.id,
            InmateUpdate(),
            is_enrolled=True,
            enrolled_at=enrolled_at,
        )

        assert updated.is_enrolled is True
        assert updated.enrolled_at == enrolled_at


class TestInmateRepositoryDelete:
    """Test deleting inmate records."""

    def test_delete_success(self, inmate_repo, sample_inmate_data):
        """Should delete inmate."""
        created = inmate_repo.create(sample_inmate_data)
        result = inmate_repo.delete(created.id)

        assert result is True
        assert inmate_repo.get_by_id(created.id) is None

    def test_delete_not_found(self, inmate_repo):
        """Should return False when deleting non-existent inmate."""
        result = inmate_repo.delete("non-existent-id")
        assert result is False
