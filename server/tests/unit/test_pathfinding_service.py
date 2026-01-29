"""
Tests for PathfindingService.

Tests route optimization and shortest path calculations.
"""
import pytest

from app.services.pathfinding_service import PathfindingService, RouteStop, OptimizedRoute


@pytest.fixture
def pathfinding_service(test_db):
    """Create PathfindingService with test database."""
    from app.db.database import get_connection
    from app.db.repositories.connection_repo import ConnectionRepository
    from app.db.repositories.location_repo import LocationRepository
    from app.models.location import LocationCreate, LocationType, LocationConnectionCreate
    
    conn = get_connection(test_db)
    
    # Create test locations
    location_repo = LocationRepository(conn)
    locations = []
    for i in range(1, 6):
        loc = location_repo.create(LocationCreate(
            name=f"Test Location {i}",
            type=LocationType.CELL,
            building="Block A" if i <= 3 else "Block B",
            floor=(i - 1) % 3,
            capacity=1
        ))
        locations.append(loc)
    
    # Create connections (graph structure)
    # loc-1 -- loc-2 -- loc-3 (Block A, sequential)
    #           |
    #          loc-4 -- loc-5 (Block B)
    connection_repo = ConnectionRepository(conn)
    connection_repo.create(LocationConnectionCreate(
        from_location_id=locations[0].id,
        to_location_id=locations[1].id,
        distance_meters=10,
        travel_time_seconds=15,
        connection_type="corridor",
        is_bidirectional=True
    ))
    connection_repo.create(LocationConnectionCreate(
        from_location_id=locations[1].id,
        to_location_id=locations[2].id,
        distance_meters=10,
        travel_time_seconds=15,
        connection_type="corridor",
        is_bidirectional=True
    ))
    connection_repo.create(LocationConnectionCreate(
        from_location_id=locations[1].id,
        to_location_id=locations[3].id,
        distance_meters=50,
        travel_time_seconds=60,
        connection_type="walkway",
        is_bidirectional=True
    ))
    connection_repo.create(LocationConnectionCreate(
        from_location_id=locations[3].id,
        to_location_id=locations[4].id,
        distance_meters=10,
        travel_time_seconds=15,
        connection_type="corridor",
        is_bidirectional=True
    ))
    
    return PathfindingService(connection_repo, location_repo), locations


class TestPathfindingService:
    """Test suite for PathfindingService."""

    def test_calculate_route_orders_locations_logically(
        self, pathfinding_service
    ):
        """Should order locations by building then floor."""
        service, locations = pathfinding_service
        
        # Request route visiting locations in random order
        location_ids = [locations[2].id, locations[0].id, locations[4].id]
        
        result = service.calculate_route(location_ids)
        
        assert isinstance(result, OptimizedRoute)
        assert len(result.stops) == 3
        # Should be ordered logically (Block A first, then Block B)
        
    def test_calculate_route_includes_walking_directions(
        self, pathfinding_service
    ):
        """Should include walking directions between stops."""
        service, locations = pathfinding_service
        
        location_ids = [locations[0].id, locations[1].id]
        
        result = service.calculate_route(location_ids)
        
        assert len(result.stops) == 2
        # First stop has no previous
        assert result.stops[0].walking_from_previous is None or result.stops[0].walking_from_previous.distance_meters == 0
        # Second stop has walking info
        assert result.stops[1].walking_from_previous is not None
        assert result.stops[1].walking_from_previous.distance_meters == 10

    def test_calculate_route_total_time_is_sum(
        self, pathfinding_service
    ):
        """Should calculate total time as sum of walking times."""
        service, locations = pathfinding_service
        
        location_ids = [locations[0].id, locations[1].id, locations[2].id]
        
        result = service.calculate_route(location_ids)
        
        assert result.total_time_seconds == 30  # 15 + 15

    def test_calculate_route_empty_returns_empty_route(
        self, pathfinding_service
    ):
        """Should return empty route for empty input."""
        service, locations = pathfinding_service
        
        result = service.calculate_route([])
        
        assert len(result.stops) == 0
        assert result.total_time_seconds == 0
        assert result.total_distance_meters == 0

    def test_calculate_route_single_location(
        self, pathfinding_service
    ):
        """Should handle single location."""
        service, locations = pathfinding_service
        
        result = service.calculate_route([locations[0].id])
        
        assert len(result.stops) == 1
        assert result.total_time_seconds == 0
        assert result.total_distance_meters == 0

    def test_find_shortest_path_adjacent_locations(
        self, pathfinding_service
    ):
        """Should find direct path between adjacent locations."""
        service, locations = pathfinding_service
        
        path = service.find_shortest_path(locations[0].id, locations[1].id)
        
        assert path is not None
        assert len(path) == 2
        assert path[0] == locations[0].id
        assert path[1] == locations[1].id

    def test_find_shortest_path_distant_locations(
        self, pathfinding_service
    ):
        """Should find path through multiple nodes."""
        service, locations = pathfinding_service
        
        # Path from loc-1 to loc-5 goes through loc-2 and loc-4
        path = service.find_shortest_path(locations[0].id, locations[4].id)
        
        assert path is not None
        assert len(path) == 4
        assert path[0] == locations[0].id
        assert path[-1] == locations[4].id

    def test_find_shortest_path_no_connection_returns_none(
        self, pathfinding_service
    ):
        """Should return None when no path exists."""
        service, locations = pathfinding_service
        
        # Create an isolated location with no connections
        from app.db.repositories.location_repo import LocationRepository
        from app.models.location import LocationCreate, LocationType
        location_repo = LocationRepository(service.connection_repo.conn)
        isolated = location_repo.create(LocationCreate(
            name="Isolated Location",
            type=LocationType.CELL,
            building="Block C",
            floor=0,
            capacity=1
        ))
        
        path = service.find_shortest_path(locations[0].id, isolated.id)
        
        assert path is None

    def test_get_walking_directions(
        self, pathfinding_service
    ):
        """Should provide human-readable walking directions."""
        service, locations = pathfinding_service
        
        directions = service.get_walking_directions(
            locations[1].id, locations[3].id
        )
        
        assert directions is not None
        assert directions.distance_meters == 50
        assert directions.time_seconds == 60
        assert "walkway" in directions.description.lower()
