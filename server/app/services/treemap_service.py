"""
Treemap service for rollcall visualization.

Provides business logic for generating hierarchical treemap data showing
rollcall verification status across the prison hierarchy.
"""
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set

from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.rollcall_repo import RollCallRepository
from app.db.repositories.verification_repo import VerificationRepository
from app.models.location import Location, LocationType
from app.models.rollcall import RollCall, RouteStop
from app.models.treemap import InmateVerification, TreemapMetadata, TreemapNode, TreemapResponse
from app.models.verification import Verification, VerificationStatus


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
        self.verification_repo = VerificationRepository(conn)

    def build_treemap_hierarchy(
        self, rollcall_ids: List[str], timestamp: datetime, include_empty: bool = False
    ) -> TreemapResponse:
        """
        Build hierarchical treemap structure for multiple rollcalls at a given timestamp.

        Args:
            rollcall_ids: List of rollcall IDs to include (empty list = show all locations)
            timestamp: Point in time to show status
            include_empty: If True, include locations with no inmates

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

        # Fetch all verifications for all rollcalls (if any specified)
        all_verifications = []
        if rollcall_ids:
            for rollcall_id in rollcall_ids:
                verifications = self.verification_repo.get_by_roll_call(rollcall_id)
                all_verifications.extend(verifications)

        # Build location hierarchy starting from prisons
        prisons = self._get_prison_locations()

        if not prisons:
            # Fallback: build from houseblocks if no prisons exist
            return self._build_from_houseblocks(
                rollcalls, estimated_times_map, all_verifications, timestamp, include_empty
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

    def determine_location_status(
        self,
        location: Location,
        rollcalls: List[RollCall],
        estimated_times_map: Dict[str, Dict[str, datetime]],
        verifications: List[Verification],
        timestamp: datetime,
    ) -> str:
        """
        Determine status of a location at a given timestamp.

        Status rules:
        - GREY: Location not in any rollcall route
        - AMBER: Rollcall scheduled at timestamp but not completed
        - GREEN: Rollcall completed AND all inmates verified
        - RED: Rollcall completed BUT any inmate failed verification

        Args:
            location: Location to check
            rollcalls: List of rollcalls
            estimated_times_map: Map of rollcall_id -> location_id -> estimated time
            verifications: All verification records
            timestamp: Point in time to check

        Returns:
            Status string: grey, amber, green, red
        """
        # Check if location is in any rollcall route
        location_in_route = False
        is_scheduled = False
        is_completed = False
        has_failed_verification = False
        has_any_verification = False

        for rollcall in rollcalls:
            estimated_times = estimated_times_map.get(rollcall.id, {})

            if location.id not in estimated_times:
                continue

            location_in_route = True
            estimated_time = estimated_times[location.id]

            # Check if timestamp is within scheduled window (±10 minutes)
            time_diff = abs((timestamp - estimated_time).total_seconds() / 60)

            if time_diff <= 10:
                is_scheduled = True

            # Check verifications for this location and rollcall
            location_verifications = [
                v for v in verifications
                if v.location_id == location.id and v.roll_call_id == rollcall.id
            ]

            if location_verifications:
                has_any_verification = True
                # Check if any verification failed
                for v in location_verifications:
                    if v.status in [
                        VerificationStatus.NOT_FOUND,
                        VerificationStatus.WRONG_LOCATION,
                    ]:
                        has_failed_verification = True
                        break

                # If we have verifications and timestamp is after scheduled time,
                # consider it completed
                if timestamp >= estimated_time:
                    is_completed = True

        # Determine status based on rules
        if not location_in_route:
            return "grey"

        if has_failed_verification:
            return "red"

        if is_completed and has_any_verification:
            return "green"

        if is_scheduled or (location_in_route and not is_completed):
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
    ) -> TreemapResponse:
        """
        Fallback: build treemap from houseblocks if no prisons exist.

        Args:
            rollcalls: List of rollcalls
            estimated_times_map: Map of estimated times
            verifications: All verifications
            timestamp: Point in time

        Returns:
            TreemapResponse rooted at "All Facilities"
        """
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
    ) -> Optional[TreemapNode]:
        """
        Recursively build a subtree for a location.

        Args:
            location: Root location for this subtree
            rollcalls: List of rollcalls
            estimated_times_map: Map of estimated times
            verifications: All verifications
            timestamp: Point in time

        Returns:
            TreemapNode or None if location has no inmates/children
        """
        # Get child locations
        children_nodes = []
        cursor = self.conn.execute(
            "SELECT * FROM locations WHERE parent_id = ?",
            (location.id,),
        )
        rows = cursor.fetchall()

        child_locations = []
        for row in rows:
            child_locations.append(
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

        # Recursively build children
        for child in child_locations:
            child_node = self._build_location_subtree(
                child,
                rollcalls,
                estimated_times_map,
                verifications,
                timestamp,
                include_empty,
            )
            if child_node:
                children_nodes.append(child_node)

        # Get inmates at this location (for cells)
        inmate_count = 0
        verified_count = 0
        failed_count = 0
        inmate_details: List[InmateVerification] = []

        if location.type == LocationType.CELL:
            inmates = self.inmate_repo.get_by_home_cell(location.id)
            inmate_count = len(inmates)

            # Build inmate details with verification status
            for inmate in inmates:
                # Find verification for this inmate at this location
                inmate_verification = None
                for v in verifications:
                    if v.location_id == location.id and v.expected_inmate_id == inmate.id:
                        inmate_verification = v
                        break

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

        # Calculate value (inmate count)
        if location.type == LocationType.CELL:
            value = inmate_count
        else:
            # For parent nodes, sum children values
            value = sum(child.value for child in children_nodes)

        # If no inmates and no children, skip this location (unless include_empty is True)
        if not include_empty and value == 0 and not children_nodes:
            return None

        # Determine status
        if children_nodes:
            # Aggregate from children
            children_statuses = [child.status for child in children_nodes]
            status = self.aggregate_status_upward(children_statuses)

            # Sum metadata from children
            for child in children_nodes:
                if child.metadata:
                    inmate_count += child.metadata.inmate_count
                    verified_count += child.metadata.verified_count
                    failed_count += child.metadata.failed_count
        else:
            # Leaf node (cell)
            status = self.determine_location_status(
                location,
                rollcalls,
                estimated_times_map,
                verifications,
                timestamp,
            )

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
