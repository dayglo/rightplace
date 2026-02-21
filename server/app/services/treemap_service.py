"""
Treemap service for rollcall visualization.

Provides business logic for generating hierarchical treemap data showing
rollcall verification status across the prison hierarchy.
"""
import sqlite3
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Set

from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.rollcall_repo import RollCallRepository
from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.verification_repo import VerificationRepository
from app.models.location import Location, LocationType
from app.models.rollcall import RollCall, RouteStop
from app.models.treemap import InmateVerification, TreemapMetadata, TreemapNode, TreemapResponse
from app.models.verification import Verification, VerificationStatus


class OccupancyMode(str, Enum):
    """Mode for determining inmate locations in treemap."""

    SCHEDULED = "scheduled"  # Use schedule data - inmates at their scheduled location
    HOME_CELL = "home_cell"  # Use home cell assignments - inmates always in their cell


class TreemapService:
    """Service for building treemap visualization data."""

    # Default average duration per stop in minutes
    DEFAULT_AVG_DURATION_PER_STOP = 5

    def __init__(self, conn: sqlite3.Connection):
        """
        Initialize treemap service.

        Args:
            conn: Database connection
        """
        self.conn = conn
        self.location_repo = LocationRepository(conn)
        self.inmate_repo = InmateRepository(conn)
        self.rollcall_repo = RollCallRepository(conn)
        self.schedule_repo = ScheduleRepository(conn)
        self.verification_repo = VerificationRepository(conn)

        # PERFORMANCE OPTIMIZATION: Cache location hierarchy (parent-child map)
        # Location hierarchy is static - build once, reuse for all requests
        self._location_hierarchy_cache: Optional[Dict[Optional[str], List[Location]]] = None

    def _get_location_hierarchy(self) -> Dict[Optional[str], List[Location]]:
        """
        Get cached location hierarchy (parent-child map) or build it if not cached.

        Returns:
            Dict mapping parent_id to list of child locations
        """
        if self._location_hierarchy_cache is None:
            # Build parent-child map from all locations
            all_locations = self.location_repo.get_all()
            parent_child_map: Dict[Optional[str], List[Location]] = {}
            for loc in all_locations:
                if loc.parent_id not in parent_child_map:
                    parent_child_map[loc.parent_id] = []
                parent_child_map[loc.parent_id].append(loc)
            self._location_hierarchy_cache = parent_child_map

        return self._location_hierarchy_cache

    def invalidate_location_cache(self) -> None:
        """
        Invalidate the location hierarchy cache.

        Call this when locations are added, removed, or modified.
        """
        self._location_hierarchy_cache = None

    def build_treemap_hierarchy(
        self,
        rollcall_ids: List[str],
        timestamp: datetime,
        include_empty: bool = False,
        occupancy_mode: OccupancyMode = OccupancyMode.SCHEDULED,
        filter_to_route: bool = False,
    ) -> TreemapResponse:
        """
        Build hierarchical treemap structure for multiple rollcalls at a given timestamp.

        Args:
            rollcall_ids: List of rollcall IDs to include (empty list = show all locations)
            timestamp: Point in time to show status
            include_empty: If True, include locations with no inmates
            occupancy_mode: How to determine inmate locations (scheduled or home_cell)
            filter_to_route: If True, only include locations in rollcall routes and their descendants

        Returns:
            TreemapResponse with root node and children
        """
        # Fetch all rollcalls (if any specified)
        rollcalls = []
        if rollcall_ids:
            for rc_id in rollcall_ids:
                rollcall = self.rollcall_repo.get_by_id(rc_id)
                if rollcall:  # Only add if rollcall exists
                    rollcalls.append(rollcall)

        # Calculate estimated times for all rollcalls
        estimated_times_map = {}
        for rollcall in rollcalls:
            estimated_times_map[rollcall.id] = self.calculate_estimated_times(rollcall)

        # Fetch all verifications for all rollcalls up to the given timestamp
        # This filters verifications to only show those that occurred BEFORE the timestamp
        all_verifications = []
        if rollcall_ids:
            for rollcall_id in rollcall_ids:
                verifications = self.verification_repo.get_by_roll_call_before_timestamp(
                    rollcall_id, timestamp
                )
                all_verifications.extend(verifications)

        # PERFORMANCE OPTIMIZATION: Build verification hash map for O(1) lookups
        # This eliminates nested loops O(n*m) -> O(n)
        verification_map: Dict[tuple[str, str], Verification] = {}
        for v in all_verifications:
            key = (v.location_id, v.inmate_id)
            verification_map[key] = v

        # Build location -> inmates map based on occupancy mode
        location_inmates_map = self._build_location_inmates_map(timestamp, occupancy_mode)

        # PERFORMANCE OPTIMIZATION: Get cached parent-child map or build it
        # This eliminates 4,912 separate database queries (one per location)
        parent_child_map = self._get_location_hierarchy()

        # Build allowed locations set if filtering to route
        allowed_locations: Optional[Set[str]] = None
        if filter_to_route and rollcalls:
            allowed_locations = self._build_route_location_set(rollcalls, parent_child_map)

        # Build location hierarchy starting from prisons
        prisons = self._get_prison_locations()

        if not prisons:
            # Fallback: build from houseblocks if no prisons exist
            return self._build_from_houseblocks(
                rollcalls,
                estimated_times_map,
                all_verifications,
                timestamp,
                include_empty,
                location_inmates_map,
                parent_child_map,
                verification_map,
            )

        # Build children for root node (all prisons)
        children = []
        total_value = 0

        for prison in prisons:
            prison_node = self._build_location_subtree(
                prison,
                rollcalls,
                estimated_times_map,
                all_verifications,
                timestamp,
                include_empty,
                location_inmates_map,
                parent_child_map,
                verification_map,
                allowed_locations,
            )
            if prison_node:
                children.append(prison_node)
                total_value += prison_node.value

        return TreemapResponse(
            name="All Prisons",
            type="root",
            value=total_value,
            children=children,
        )

    def calculate_estimated_times(
        self, rollcall: RollCall
    ) -> Dict[str, datetime]:
        """
        Calculate estimated arrival times for each RouteStop in a rollcall.

        Args:
            rollcall: RollCall with route

        Returns:
            Dict mapping location_id to estimated arrival time
        """
        estimated_times = {}

        for stop in rollcall.route:
            # Estimate arrival = scheduled_at + (stop.order * avg_duration_per_stop)
            minutes_offset = stop.order * self.DEFAULT_AVG_DURATION_PER_STOP
            estimated_arrival = rollcall.scheduled_at + timedelta(minutes=minutes_offset)
            estimated_times[stop.location_id] = estimated_arrival

        return estimated_times

    def _build_location_inmates_map(
        self, timestamp: datetime, occupancy_mode: OccupancyMode
    ) -> Dict[str, List]:
        """
        Build a map of location_id to list of inmates at that location.

        Args:
            timestamp: Point in time to check
            occupancy_mode: How to determine inmate locations

        Returns:
            Dict mapping location_id to list of Inmate objects
        """
        from app.models.inmate import Inmate

        location_inmates: Dict[str, List] = {}

        if occupancy_mode == OccupancyMode.HOME_CELL:
            # Use home cell assignments - get all inmates and group by home_cell_id
            all_inmates = self.inmate_repo.get_all()
            for inmate in all_inmates:
                if inmate.home_cell_id:
                    if inmate.home_cell_id not in location_inmates:
                        location_inmates[inmate.home_cell_id] = []
                    location_inmates[inmate.home_cell_id].append(inmate)
        else:
            # SCHEDULED mode - inmates at scheduled location, or home cell if no schedule
            day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
            time_str = timestamp.strftime("%H:%M")

            # Get all inmates
            all_inmates = self.inmate_repo.get_all()

            # Get schedule entries active at this time
            schedule_entries = self.schedule_repo.get_at_time(day_of_week, time_str)

            # Build a map of inmate_id -> scheduled location
            scheduled_locations: Dict[str, str] = {}
            for entry in schedule_entries:
                scheduled_locations[entry.inmate_id] = entry.location_id

            # Place each inmate at their scheduled location or home cell
            for inmate in all_inmates:
                if inmate.id in scheduled_locations:
                    # Inmate has a schedule entry - use scheduled location
                    location_id = scheduled_locations[inmate.id]
                elif inmate.home_cell_id:
                    # No schedule entry - fall back to home cell
                    location_id = inmate.home_cell_id
                else:
                    # No schedule and no home cell - skip
                    continue

                if location_id not in location_inmates:
                    location_inmates[location_id] = []
                location_inmates[location_id].append(inmate)

        return location_inmates

    def determine_location_status(
        self,
        location: Location,
        rollcalls: List[RollCall],
        estimated_times_map: Dict[str, Dict[str, datetime]],
        verifications: List[Verification],
        timestamp: datetime,
        inmate_count: int = 0,
        verified_count: int = 0,
        failed_count: int = 0,
    ) -> str:
        """
        Determine status of a location at a given timestamp.

        Status rules:
        - RED: Any inmate failed verification (not_found or wrong_location)
        - GREEN: All inmates verified (verified_count == inmate_count)
        - AMBER: Some inmates verified (partial progress) OR scheduled but not started
        - GREY: Location not in any rollcall route or no inmates

        Args:
            location: Location to check
            rollcalls: List of rollcalls
            estimated_times_map: Map of rollcall_id -> location_id -> estimated time
            verifications: All verification records
            timestamp: Point in time to check
            inmate_count: Total inmates expected at this location
            verified_count: Number of inmates verified so far
            failed_count: Number of failed verifications

        Returns:
            Status string: grey, amber, green, red
        """
        # Priority 1: Failed verifications = RED
        if failed_count > 0:
            return "red"

        # Priority 2: All verified = GREEN
        if inmate_count > 0 and verified_count == inmate_count:
            return "green"

        # Priority 3: Partial verification = AMBER
        if verified_count > 0 and verified_count < inmate_count:
            return "amber"

        # Check if location is in any rollcall route
        location_in_route = False
        is_scheduled = False

        for rollcall in rollcalls:
            estimated_times = estimated_times_map.get(rollcall.id, {})

            # Check if location is in route
            if location.id in estimated_times:
                location_in_route = True
                estimated_time = estimated_times[location.id]

                # Check if timestamp is within scheduled window (±10 minutes)
                time_diff = abs((timestamp - estimated_time).total_seconds() / 60)

                if time_diff <= 10:
                    is_scheduled = True

        # Priority 4: Scheduled but not started = AMBER
        if is_scheduled or (location_in_route and inmate_count > 0):
            return "amber"

        return "grey"

    def aggregate_status_upward(
        self, children_statuses: List[str]
    ) -> str:
        """
        Aggregate status from children to parent.

        Rules:
        - If any child is RED → parent is RED
        - If all children are GREEN → parent is GREEN
        - If any child is AMBER and no RED → parent is AMBER
        - If all children are GREY → parent is GREY

        Args:
            children_statuses: List of child status strings

        Returns:
            Aggregated status string
        """
        if not children_statuses:
            return "grey"

        if "red" in children_statuses:
            return "red"

        if all(s == "green" for s in children_statuses):
            return "green"

        if "amber" in children_statuses:
            return "amber"

        return "grey"

    def _build_route_location_set(
        self,
        rollcalls: List[RollCall],
        parent_child_map: Dict[Optional[str], List[Location]],
    ) -> Set[str]:
        """
        Build set of location IDs that are in the rollcall routes or their descendants/ancestors.

        This is used for filter_to_route to only show relevant locations.

        Args:
            rollcalls: List of rollcalls to get routes from
            parent_child_map: Pre-built map of parent_id -> child locations

        Returns:
            Set of location IDs to include in the filtered treemap
        """
        allowed: Set[str] = set()

        # Get all route location IDs
        route_location_ids: Set[str] = set()
        for rollcall in rollcalls:
            for stop in rollcall.route:
                route_location_ids.add(stop.location_id)

        # For each route location, add it and all descendants
        def add_descendants(location_id: str) -> None:
            allowed.add(location_id)
            children = parent_child_map.get(location_id, [])
            for child in children:
                add_descendants(child.id)

        for loc_id in route_location_ids:
            add_descendants(loc_id)

        # Also add all ancestors (parent chain) so tree structure is complete
        # Build a reverse lookup: location_id -> location
        all_locations = self.location_repo.get_all()
        location_by_id = {loc.id: loc for loc in all_locations}

        def add_ancestors(location_id: str) -> None:
            loc = location_by_id.get(location_id)
            if loc and loc.parent_id:
                allowed.add(loc.parent_id)
                add_ancestors(loc.parent_id)

        for loc_id in route_location_ids:
            add_ancestors(loc_id)

        return allowed

    def _get_prison_locations(self) -> List[Location]:
        """Get all locations of type PRISON."""
        cursor = self.conn.execute(
            "SELECT * FROM locations WHERE type = ?",
            (LocationType.PRISON.value,),
        )
        rows = cursor.fetchall()

        locations = []
        for row in rows:
            locations.append(
                Location(
                    id=row[0],
                    name=row[1],
                    type=LocationType(row[2]),
                    parent_id=row[3],
                    capacity=row[4],
                    floor=row[5],
                    building=row[6],
                )
            )
        return locations

    def _build_from_houseblocks(
        self,
        rollcalls: List[RollCall],
        estimated_times_map: Dict[str, Dict[str, datetime]],
        verifications: List[Verification],
        timestamp: datetime,
        include_empty: bool = False,
        location_inmates_map: Optional[Dict[str, List]] = None,
        parent_child_map: Optional[Dict[Optional[str], List[Location]]] = None,
        verification_map: Optional[Dict[tuple[str, str], Verification]] = None,
    ) -> TreemapResponse:
        """
        Fallback: build treemap from houseblocks if no prisons exist.

        Args:
            rollcalls: List of rollcalls
            estimated_times_map: Map of estimated times
            verifications: All verifications
            timestamp: Point in time
            include_empty: If True, include locations with no inmates
            location_inmates_map: Map of location_id to list of inmates at that location
            parent_child_map: Map of parent_id to list of child locations (for performance)
            verification_map: Map of (location_id, inmate_id) to verification (for performance)

        Returns:
            TreemapResponse rooted at "All Facilities"
        """
        if location_inmates_map is None:
            location_inmates_map = {}

        # Get all houseblocks
        cursor = self.conn.execute(
            "SELECT * FROM locations WHERE type = ? AND parent_id IS NULL",
            (LocationType.HOUSEBLOCK.value,),
        )
        rows = cursor.fetchall()

        houseblocks = []
        for row in rows:
            houseblocks.append(
                Location(
                    id=row[0],
                    name=row[1],
                    type=LocationType(row[2]),
                    parent_id=row[3],
                    capacity=row[4],
                    floor=row[5],
                    building=row[6],
                )
            )

        children = []
        total_value = 0

        for houseblock in houseblocks:
            hb_node = self._build_location_subtree(
                houseblock,
                rollcalls,
                estimated_times_map,
                verifications,
                timestamp,
                include_empty,
                location_inmates_map,
                parent_child_map,
                verification_map,
            )
            if hb_node:
                children.append(hb_node)
                total_value += hb_node.value

        return TreemapResponse(
            name="All Facilities",
            type="root",
            value=total_value,
            children=children,
        )

    def _build_location_subtree(
        self,
        location: Location,
        rollcalls: List[RollCall],
        estimated_times_map: Dict[str, Dict[str, datetime]],
        verifications: List[Verification],
        timestamp: datetime,
        include_empty: bool = False,
        location_inmates_map: Optional[Dict[str, List]] = None,
        parent_child_map: Optional[Dict[Optional[str], List[Location]]] = None,
        verification_map: Optional[Dict[tuple[str, str], Verification]] = None,
        allowed_locations: Optional[Set[str]] = None,
    ) -> Optional[TreemapNode]:
        """
        Recursively build a subtree for a location.

        Args:
            location: Root location for this subtree
            rollcalls: List of rollcalls
            estimated_times_map: Map of estimated times
            verifications: All verifications
            timestamp: Point in time
            include_empty: If True, include locations with no inmates
            location_inmates_map: Map of location_id to list of inmates at that location
            parent_child_map: Map of parent_id to list of child locations (for performance)
            verification_map: Map of (location_id, inmate_id) to verification (for performance)

        Returns:
            TreemapNode or None if location has no inmates/children
        """
        if location_inmates_map is None:
            location_inmates_map = {}
        if parent_child_map is None:
            parent_child_map = {}
        if verification_map is None:
            verification_map = {}

        # If filtering to route, skip locations not in the allowed set
        # (but still process if allowed_locations is None - means no filtering)
        if allowed_locations is not None and location.id not in allowed_locations:
            return None

        # Get child locations from the parent-child map (performance optimization)
        # This eliminates 4,912 separate database queries!
        children_nodes = []
        child_locations = parent_child_map.get(location.id, [])

        # Recursively build children
        for child in child_locations:
            child_node = self._build_location_subtree(
                child,
                rollcalls,
                estimated_times_map,
                verifications,
                timestamp,
                include_empty,
                location_inmates_map,
                parent_child_map,
                verification_map,
                allowed_locations,
            )
            if child_node:
                children_nodes.append(child_node)

        # Get inmates at this location (from the prebuilt map)
        # This works for ANY location type - cells, gym, education, etc.
        inmates = location_inmates_map.get(location.id, [])
        inmate_count = len(inmates)
        verified_count = 0
        failed_count = 0
        inmate_details: List[InmateVerification] = []

        # Build inmate details with verification status
        for inmate in inmates:
            # Find verification for this inmate at this location using hash map O(1) lookup
            # This replaces the nested loop which was O(n*m)
            key = (location.id, inmate.id)
            inmate_verification = verification_map.get(key)

            # Determine status
            if inmate_verification:
                if inmate_verification.status == VerificationStatus.VERIFIED:
                    verified_count += 1
                    status = "verified"
                elif inmate_verification.status == VerificationStatus.NOT_FOUND:
                    failed_count += 1
                    status = "not_found"
                elif inmate_verification.status == VerificationStatus.WRONG_LOCATION:
                    failed_count += 1
                    status = "wrong_location"
                else:
                    status = "pending"
            else:
                status = "pending"

            inmate_details.append(
                InmateVerification(
                    inmate_id=inmate.id,
                    name=f"{inmate.first_name} {inmate.last_name}",
                    status=status,
                )
            )

        # Calculate value: direct inmates at this location + sum of children
        direct_value = inmate_count
        children_value = sum(child.value for child in children_nodes)
        value = direct_value + children_value

        # If no inmates at this location or any descendants, skip it
        # (unless include_empty is True)
        if not include_empty and value == 0:
            return None

        # Determine status
        if children_nodes or inmate_count > 0:
            # Collect statuses from children and this node's direct inmates
            all_statuses = [child.status for child in children_nodes]

            # If this location has direct inmates, determine its own status
            if inmate_count > 0:
                direct_status = self.determine_location_status(
                    location,
                    rollcalls,
                    estimated_times_map,
                    verifications,
                    timestamp,
                    inmate_count=len(inmates),  # Direct inmate count (not aggregated)
                    verified_count=verified_count,
                    failed_count=failed_count,
                )
                all_statuses.append(direct_status)

            status = self.aggregate_status_upward(all_statuses) if all_statuses else "grey"

            # Sum metadata from children
            for child in children_nodes:
                if child.metadata:
                    inmate_count += child.metadata.inmate_count
                    verified_count += child.metadata.verified_count
                    failed_count += child.metadata.failed_count
        else:
            # No children and no inmates - grey status
            status = "grey"

        # Build metadata
        metadata = TreemapMetadata(
            inmate_count=inmate_count,
            verified_count=verified_count,
            failed_count=failed_count,
            inmates=inmate_details if inmate_details else None,
        )

        # Build node
        return TreemapNode(
            id=location.id,
            name=location.name,
            type=location.type.value,
            value=value,
            status=status,
            children=children_nodes if children_nodes else None,
            metadata=metadata,
        )
