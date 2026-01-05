"""
Test suite for LocationRepository.

Tests CRUD operations for location data.
"""
from uuid import uuid4

import pytest

from app.db.database import get_connection, init_db
from app.db.repositories.location_repo import LocationRepository
from app.models.location import Location, LocationType, LocationCreate, LocationUpdate


@pytest.fixture
def db_conn():
    """Create an in-memory database connection for testing."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def location_repo(db_conn):
    """Create a LocationRepository instance."""
    return LocationRepository(db_conn)


class TestLocationRepositoryCreate:
    """Test location creation."""

    def test_create_location_success(self, location_repo):
        """Should create location with all fields."""
        location_data = LocationCreate(
            name="Cell Block A",
            type=LocationType.BLOCK,
            building="Main",
            parent_id=None,
            capacity=50,
            floor=1,
        )
        location = location_repo.create(location_data)

        assert location.id is not None
        assert location.name == "Cell Block A"
        assert location.type == LocationType.BLOCK
        assert location.building == "Main"
        assert location.parent_id is None
        assert location.capacity == 50
        assert location.floor == 1

    def test_create_location_with_defaults(self, location_repo):
        """Should create location with default values."""
        location_data = LocationCreate(
            name="Cell A-101",
            type=LocationType.CELL,
            building="Main",
        )
        location = location_repo.create(location_data)

        assert location.capacity == 1
        assert location.floor == 0
        assert location.parent_id is None

    def test_create_location_with_parent(self, location_repo):
        """Should create location with parent relationship."""
        # Create parent location
        parent_data = LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        )
        parent = location_repo.create(parent_data)

        # Create child location
        child_data = LocationCreate(
            name="Cell A-101",
            type=LocationType.CELL,
            building="Main",
            parent_id=parent.id,
        )
        child = location_repo.create(child_data)

        assert child.parent_id == parent.id


class TestLocationRepositoryRead:
    """Test reading location records."""

    def test_get_by_id_found(self, location_repo):
        """Should retrieve location by ID."""
        location_data = LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        )
        created = location_repo.create(location_data)
        retrieved = location_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name

    def test_get_by_id_not_found(self, location_repo):
        """Should return None for non-existent ID."""
        result = location_repo.get_by_id("non-existent-id")
        assert result is None

    def test_get_all_empty(self, location_repo):
        """Should return empty list when no locations exist."""
        locations = location_repo.get_all()
        assert locations == []

    def test_get_all_multiple(self, location_repo):
        """Should return all locations."""
        location_repo.create(LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        ))
        location_repo.create(LocationCreate(
            name="Block B",
            type=LocationType.BLOCK,
            building="Main",
        ))

        locations = location_repo.get_all()
        assert len(locations) == 2

    def test_get_by_type(self, location_repo):
        """Should retrieve locations by type."""
        location_repo.create(LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        ))
        location_repo.create(LocationCreate(
            name="Cell A-101",
            type=LocationType.CELL,
            building="Main",
        ))
        location_repo.create(LocationCreate(
            name="Yard",
            type=LocationType.YARD,
            building="Main",
        ))

        blocks = location_repo.get_by_type(LocationType.BLOCK)
        assert len(blocks) == 1
        assert blocks[0].type == LocationType.BLOCK

    def test_get_by_building(self, location_repo):
        """Should retrieve locations by building."""
        location_repo.create(LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        ))
        location_repo.create(LocationCreate(
            name="Block B",
            type=LocationType.BLOCK,
            building="Main",
        ))
        location_repo.create(LocationCreate(
            name="Medical Ward",
            type=LocationType.MEDICAL,
            building="Medical",
        ))

        main_locations = location_repo.get_by_building("Main")
        assert len(main_locations) == 2
        assert all(loc.building == "Main" for loc in main_locations)

    def test_get_children(self, location_repo):
        """Should retrieve child locations."""
        # Create parent
        parent = location_repo.create(LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        ))

        # Create children
        location_repo.create(LocationCreate(
            name="Cell A-101",
            type=LocationType.CELL,
            building="Main",
            parent_id=parent.id,
        ))
        location_repo.create(LocationCreate(
            name="Cell A-102",
            type=LocationType.CELL,
            building="Main",
            parent_id=parent.id,
        ))

        # Create unrelated location
        location_repo.create(LocationCreate(
            name="Block B",
            type=LocationType.BLOCK,
            building="Main",
        ))

        children = location_repo.get_children(parent.id)
        assert len(children) == 2
        assert all(child.parent_id == parent.id for child in children)


class TestLocationRepositoryUpdate:
    """Test updating location records."""

    def test_update_success(self, location_repo):
        """Should update location fields."""
        created = location_repo.create(LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
            capacity=50,
        ))

        update_data = LocationUpdate(
            name="Block A (Renovated)",
            capacity=60,
        )
        updated = location_repo.update(created.id, update_data)

        assert updated is not None
        assert updated.id == created.id
        assert updated.name == "Block A (Renovated)"
        assert updated.capacity == 60
        assert updated.building == "Main"  # Unchanged

    def test_update_partial(self, location_repo):
        """Should update only specified fields."""
        created = location_repo.create(LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        ))

        update_data = LocationUpdate(name="Block A+")
        updated = location_repo.update(created.id, update_data)

        assert updated.name == "Block A+"
        assert updated.type == LocationType.BLOCK  # Unchanged

    def test_update_not_found(self, location_repo):
        """Should return None when updating non-existent location."""
        update_data = LocationUpdate(name="New Name")
        result = location_repo.update("non-existent-id", update_data)
        assert result is None


class TestLocationRepositoryDelete:
    """Test deleting location records."""

    def test_delete_success(self, location_repo):
        """Should delete location."""
        created = location_repo.create(LocationCreate(
            name="Block A",
            type=LocationType.BLOCK,
            building="Main",
        ))
        result = location_repo.delete(created.id)

        assert result is True
        assert location_repo.get_by_id(created.id) is None

    def test_delete_not_found(self, location_repo):
        """Should return False when deleting non-existent location."""
        result = location_repo.delete("non-existent-id")
        assert result is False
