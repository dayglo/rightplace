"""
Pathfinding service for route optimization.

Uses Dijkstra's algorithm for shortest paths and logical ordering
for route calculation through the prison facility.
"""
import heapq
from dataclasses import dataclass
from typing import Optional

from app.db.repositories.connection_repo import ConnectionRepository
from app.db.repositories.location_repo import LocationRepository


@dataclass
class WalkingDirections:
    """Walking directions between two locations."""
    distance_meters: int
    time_seconds: int
    description: str
    connection_type: str


@dataclass
class RouteStop:
    """A stop in an optimized route."""
    location_id: str
    location_name: str
    building: str
    floor: int
    order: int
    walking_from_previous: Optional[WalkingDirections]


@dataclass 
class OptimizedRoute:
    """An optimized route through locations."""
    stops: list[RouteStop]
    total_distance_meters: int
    total_time_seconds: int


class PathfindingService:
    """Service for calculating optimal routes through the facility."""

    def __init__(
        self,
        connection_repo: ConnectionRepository,
        location_repo: LocationRepository
    ):
        """
        Initialize service with repositories.

        Args:
            connection_repo: Repository for location connections
            location_repo: Repository for locations
        """
        self.connection_repo = connection_repo
        self.location_repo = location_repo

    def calculate_route(self, location_ids: list[str]) -> OptimizedRoute:
        """
        Calculate an optimized route visiting all specified locations.

        Orders locations logically by building then floor, then calculates
        walking directions between consecutive stops.

        Args:
            location_ids: List of location IDs to visit

        Returns:
            OptimizedRoute with ordered stops and total time/distance
        """
        if not location_ids:
            return OptimizedRoute(stops=[], total_distance_meters=0, total_time_seconds=0)

        # Get location details for sorting
        locations = {}
        for loc_id in location_ids:
            loc = self.location_repo.get_by_id(loc_id)
            if loc:
                locations[loc_id] = loc

        if not locations:
            return OptimizedRoute(stops=[], total_distance_meters=0, total_time_seconds=0)

        # Sort locations logically: by building, then floor, then name
        sorted_ids = sorted(
            locations.keys(),
            key=lambda lid: (
                locations[lid].building,
                locations[lid].floor,
                locations[lid].name
            )
        )

        # Build route stops with walking directions
        stops = []
        total_distance = 0
        total_time = 0
        prev_id = None

        for order, loc_id in enumerate(sorted_ids):
            loc = locations[loc_id]
            walking = None

            if prev_id:
                walking = self.get_walking_directions(prev_id, loc_id)
                if walking:
                    total_distance += walking.distance_meters
                    total_time += walking.time_seconds

            stops.append(RouteStop(
                location_id=loc_id,
                location_name=loc.name,
                building=loc.building,
                floor=loc.floor,
                order=order,
                walking_from_previous=walking
            ))
            prev_id = loc_id

        return OptimizedRoute(
            stops=stops,
            total_distance_meters=total_distance,
            total_time_seconds=total_time
        )

    def find_shortest_path(
        self, start_id: str, end_id: str
    ) -> Optional[list[str]]:
        """
        Find shortest path between two locations using Dijkstra's algorithm.

        Args:
            start_id: Starting location ID
            end_id: Destination location ID

        Returns:
            List of location IDs forming the path, or None if no path exists
        """
        if start_id == end_id:
            return [start_id]

        # Build graph from connections
        graph = self.connection_repo.get_graph()

        if start_id not in graph:
            return None

        # Dijkstra's algorithm
        distances = {start_id: 0}
        previous = {start_id: None}
        pq = [(0, start_id)]
        visited = set()

        while pq:
            current_dist, current_id = heapq.heappop(pq)

            if current_id in visited:
                continue
            visited.add(current_id)

            if current_id == end_id:
                # Reconstruct path
                path = []
                node = end_id
                while node is not None:
                    path.append(node)
                    node = previous[node]
                return list(reversed(path))

            # Process neighbors
            for neighbor_id, weight in graph.get(current_id, []):
                if neighbor_id in visited:
                    continue

                new_dist = current_dist + weight
                if neighbor_id not in distances or new_dist < distances[neighbor_id]:
                    distances[neighbor_id] = new_dist
                    previous[neighbor_id] = current_id
                    heapq.heappush(pq, (new_dist, neighbor_id))

        return None  # No path found

    def get_walking_directions(
        self, from_id: str, to_id: str
    ) -> Optional[WalkingDirections]:
        """
        Get walking directions between two locations.

        Uses the connection graph to find the best path and generates
        human-readable directions.

        Args:
            from_id: Starting location ID
            to_id: Destination location ID

        Returns:
            WalkingDirections with distance, time and description
        """
        # Check for direct connection first
        connections = self.connection_repo.get_from_location(from_id)
        for conn in connections:
            if conn.to_location_id == to_id:
                from_loc = self.location_repo.get_by_id(from_id)
                to_loc = self.location_repo.get_by_id(to_id)
                return WalkingDirections(
                    distance_meters=conn.distance_meters,
                    time_seconds=conn.travel_time_seconds,
                    connection_type=conn.connection_type,
                    description=f"Walk via {conn.connection_type} to {to_loc.name if to_loc else to_id}"
                )

        # Check reverse direction for bidirectional connections
        reverse_connections = self.connection_repo.get_from_location(to_id)
        for conn in reverse_connections:
            if conn.to_location_id == from_id and conn.is_bidirectional:
                to_loc = self.location_repo.get_by_id(to_id)
                return WalkingDirections(
                    distance_meters=conn.distance_meters,
                    time_seconds=conn.travel_time_seconds,
                    connection_type=conn.connection_type,
                    description=f"Walk via {conn.connection_type} to {to_loc.name if to_loc else to_id}"
                )

        # No direct connection - find path and sum up
        path = self.find_shortest_path(from_id, to_id)
        if not path or len(path) < 2:
            return None

        total_distance = 0
        total_time = 0
        connection_types = set()

        for i in range(len(path) - 1):
            segment_dirs = self._get_direct_connection(path[i], path[i + 1])
            if segment_dirs:
                total_distance += segment_dirs.distance_meters
                total_time += segment_dirs.time_seconds
                connection_types.add(segment_dirs.connection_type)

        to_loc = self.location_repo.get_by_id(to_id)
        types_str = ", ".join(sorted(connection_types)) if connection_types else "route"

        return WalkingDirections(
            distance_meters=total_distance,
            time_seconds=total_time,
            connection_type=types_str,
            description=f"Walk via {types_str} to {to_loc.name if to_loc else to_id}"
        )

    def _get_direct_connection(
        self, from_id: str, to_id: str
    ) -> Optional[WalkingDirections]:
        """Get walking info for a direct connection."""
        connections = self.connection_repo.get_from_location(from_id)
        for conn in connections:
            if conn.to_location_id == to_id:
                return WalkingDirections(
                    distance_meters=conn.distance_meters,
                    time_seconds=conn.travel_time_seconds,
                    connection_type=conn.connection_type,
                    description=""
                )

        # Check reverse for bidirectional
        reverse = self.connection_repo.get_from_location(to_id)
        for conn in reverse:
            if conn.to_location_id == from_id and conn.is_bidirectional:
                return WalkingDirections(
                    distance_meters=conn.distance_meters,
                    time_seconds=conn.travel_time_seconds,
                    connection_type=conn.connection_type,
                    description=""
                )

        return None
