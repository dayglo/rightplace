"""
Tests for ConnectionRepository.

Tests database operations for location connections.
"""
import pytest
import sqlite3
from datetime import datetime

from app.db.repositories.connection_repo import ConnectionRepository
from app.models.location import LocationConnection, LocationConnectionCreate


@pytest.fixture
def connection_repo(test_db):
    """Create ConnectionRepository with test database."""
    from app.db.database import get_connection
    from app.db.repositories.location_repo import LocationRepository
    from app.models.location import LocationCreate, LocationType
    
    conn = get_connection(test_db)
    
    # Create test locations to satisfy foreign key constraints
    location_repo = LocationRepository(conn)
    for i in range(1, 4):
        location_repo.create(LocationCreate(
            name=f"Test Location {i}",
            type=LocationType.CELL,
            building="Test Building",
            floor=0,
            capacity=1
        ))
    
    return ConnectionRepository(conn)


@pytest.fixture
def sample_connection(connection_repo):
    """Sample connection data for testing."""
    # Get actual location IDs from the database
    from app.db.repositories.location_repo import LocationRepository
    location_repo = LocationRepository(connection_repo.conn)
    locations = location_repo.get_all()
    
    return LocationConnectionCreate(
        from_location_id=locations[0].id,
        to_location_id=locations[1].id,
        distance_meters=15,
        travel_time_seconds=30,
        connection_type="stairwell",
        is_bidirectional=True,
        requires_escort=False
    )


class TestConnectionRepository:
    """Test suite for ConnectionRepository."""

    def test_create_connection_returns_connection_with_id(
        self, connection_repo, sample_connection
    ):
        """Should create connection and return with generated ID."""
        result = connection_repo.create(sample_connection)

        assert result.id is not None
        assert result.from_location_id == sample_connection.from_location_id
        assert result.to_location_id == sample_connection.to_location_id
        assert result.distance_meters == 15
        assert result.travel_time_seconds == 30
        assert result.connection_type == "stairwell"
        assert result.is_bidirectional is True
        assert result.requires_escort is False

    def test_get_by_id_existing_returns_connection(
        self, connection_repo, sample_connection
    ):
        """Should return connection when ID exists."""
        created = connection_repo.create(sample_connection)

        result = connection_repo.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.from_location_id == sample_connection.from_location_id

    def test_get_by_id_nonexistent_returns_none(self, connection_repo):
        """Should return None when ID doesn't exist."""
        result = connection_repo.get_by_id("nonexistent-id")

        assert result is None

    def test_get_all_returns_all_connections(self, connection_repo):
        """Should return all connections."""
        # Get actual location IDs
        from app.db.repositories.location_repo import LocationRepository
        location_repo = LocationRepository(connection_repo.conn)
        locations = location_repo.get_all()
        
        conn1 = LocationConnectionCreate(
            from_location_id=locations[0].id,
            to_location_id=locations[1].id,
            distance_meters=10,
            travel_time_seconds=20
        )
        conn2 = LocationConnectionCreate(
            from_location_id=locations[1].id,
            to_location_id=locations[2].id,
            distance_meters=15,
            travel_time_seconds=30
        )

        connection_repo.create(conn1)
        connection_repo.create(conn2)

        result = connection_repo.get_all()

        assert len(result) == 2
        assert result[0].from_location_id == locations[0].id
        assert result[1].from_location_id == locations[1].id

    def test_get_from_location_returns_outgoing_connections(
        self, connection_repo
    ):
        """Should return all connections from a location."""
        # Get actual location IDs
        from app.db.repositories.location_repo import LocationRepository
        location_repo = LocationRepository(connection_repo.conn)
        locations = location_repo.get_all()
        
        conn1 = LocationConnectionCreate(
            from_location_id=locations[0].id,
            to_location_id=locations[1].id,
            distance_meters=10,
            travel_time_seconds=20
        )
        conn2 = LocationConnectionCreate(
            from_location_id=locations[0].id,
            to_location_id=locations[2].id,
            distance_meters=15,
            travel_time_seconds=30
        )
        conn3 = LocationConnectionCreate(
            from_location_id=locations[1].id,
            to_location_id=locations[2].id,
            distance_meters=20,
            travel_time_seconds=40
        )

        connection_repo.create(conn1)
        connection_repo.create(conn2)
        connection_repo.create(conn3)

        result = connection_repo.get_from_location(locations[0].id)

        assert len(result) == 2
        assert all(c.from_location_id == locations[0].id for c in result)

    def test_get_graph_returns_adjacency_list(self, connection_repo):
        """Should return graph as adjacency list with weights."""
        # Get actual location IDs
        from app.db.repositories.location_repo import LocationRepository
        location_repo = LocationRepository(connection_repo.conn)
        locations = location_repo.get_all()
        
        # Create a simple graph: loc-1 -> loc-2 -> loc-3
        conn1 = LocationConnectionCreate(
            from_location_id=locations[0].id,
            to_location_id=locations[1].id,
            distance_meters=10,
            travel_time_seconds=20,
            is_bidirectional=True
        )
        conn2 = LocationConnectionCreate(
            from_location_id=locations[1].id,
            to_location_id=locations[2].id,
            distance_meters=15,
            travel_time_seconds=30,
            is_bidirectional=False
        )

        connection_repo.create(conn1)
        connection_repo.create(conn2)

        result = connection_repo.get_graph()

        # Check bidirectional connection
        assert locations[0].id in result
        assert locations[1].id in result
        assert (locations[1].id, 20) in result[locations[0].id]  # Forward
        assert (locations[0].id, 20) in result[locations[1].id]  # Backward (bidirectional)

        # Check unidirectional connection
        assert (locations[2].id, 30) in result[locations[1].id]  # Forward only
        assert locations[2].id not in result or (locations[1].id, 30) not in result.get(locations[2].id, [])

    def test_delete_connection_returns_true_when_exists(
        self, connection_repo, sample_connection
    ):
        """Should delete connection and return True when exists."""
        created = connection_repo.create(sample_connection)

        result = connection_repo.delete(created.id)

        assert result is True
        assert connection_repo.get_by_id(created.id) is None

    def test_delete_connection_returns_false_when_not_exists(
        self, connection_repo
    ):
        """Should return False when connection doesn't exist."""
        result = connection_repo.delete("nonexistent-id")

        assert result is False
