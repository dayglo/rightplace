"""
Roll Call Generator Service.

Generates location-centric, schedule-aware roll calls with optimal routes.
"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.schedule_repo import ScheduleRepository
from app.models.inmate import Inmate
from app.models.location import Location, LocationType
from app.models.schedule import ScheduleEntry, ActivityType
from app.services.pathfinding_service import PathfindingService


@dataclass
class NextAppointment:
    """Info about a prisoner's next scheduled appointment."""
    activity_type: str
    location_id: str
    location_name: str
    start_time: str
    minutes_until: int
    is_urgent: bool  # < 30 minutes


@dataclass 
class ExpectedPrisoner:
    """A prisoner expected at a location with priority info."""
    inmate: Inmate
    home_cell_id: Optional[str]
    is_at_home_cell: bool
    current_activity: str
    next_appointment: Optional[NextAppointment]
    priority_score: int


@dataclass
class RouteStopInfo:
    """Information about a stop in the roll call route."""
    order: int
    location_id: str
    location_name: str
    location_type: str
    building: str
    floor: int
    is_occupied: bool
    expected_count: int
    walking_distance_meters: int
    walking_time_seconds: int


@dataclass
class GeneratedRollCall:
    """A generated roll call with route and summary."""
    location_ids: list[str]
    location_names: list[str]
    scheduled_at: datetime
    route: list[RouteStopInfo]
    total_locations: int
    occupied_locations: int
    empty_locations: int
    total_prisoners_expected: int
    estimated_time_seconds: int


class RollCallGeneratorService:
    """Service for generating schedule-aware roll calls."""

    def __init__(
        self,
        location_repo: LocationRepository,
        inmate_repo: InmateRepository,
        schedule_repo: ScheduleRepository,
        pathfinding_service: PathfindingService,
    ):
        """
        Initialize the generator service.

        Args:
            location_repo: Repository for location data
            inmate_repo: Repository for inmate data
            schedule_repo: Repository for schedule data
            pathfinding_service: Service for route calculation
        """
        self.location_repo = location_repo
        self.inmate_repo = inmate_repo
        self.schedule_repo = schedule_repo
        self.pathfinding_service = pathfinding_service

    def generate_roll_call(
        self,
        location_ids: list[str],
        scheduled_at: datetime,
        include_empty: bool = True,
    ) -> GeneratedRollCall:
        """
        Generate a roll call for one or more locations and their descendants.

        Args:
            location_ids: List of location IDs (can be cells, landings, wings, etc.)
            scheduled_at: When the roll call will occur
            include_empty: Whether to include empty locations in route

        Returns:
            GeneratedRollCall with route and expected prisoners

        Raises:
            ValueError: If location list is empty, location not found, or no cells found
        """
        # Validate input
        if not location_ids:
            raise ValueError("At least one location ID required")

        # Deduplicate input list while preserving order
        input_location_ids = list(dict.fromkeys(location_ids))

        # Collect all cells from all specified locations
        all_cells: list[Location] = []
        seen_cell_ids: set[str] = set()

        for location_id in input_location_ids:
            location = self.location_repo.get_by_id(location_id)
            if not location:
                raise ValueError(f"Location {location_id} not found")

            # If it's a cell, add it directly
            if location.type == LocationType.CELL:
                if location.id not in seen_cell_ids:
                    all_cells.append(location)
                    seen_cell_ids.add(location.id)
            else:
                # Get all cell descendants for non-cell locations
                descendant_cells = self.location_repo.get_all_descendants(
                    location_id, type_filter=LocationType.CELL
                )
                for cell in descendant_cells:
                    if cell.id not in seen_cell_ids:
                        all_cells.append(cell)
                        seen_cell_ids.add(cell.id)

        # Validate we found at least some cells
        if not all_cells:
            raise ValueError("No cells found in specified locations")

        # Get day of week (0=Monday, 6=Sunday)
        day_of_week = scheduled_at.weekday()
        time_str = scheduled_at.strftime("%H:%M")

        # For each cell, count expected prisoners
        location_prisoner_counts: dict[str, int] = {}
        for cell in all_cells:
            # Get prisoners whose home cell this is
            prisoners = self.inmate_repo.get_by_home_cell(cell.id)
            
            # Check schedule - are they supposed to be in cell at this time?
            expected_count = 0
            for prisoner in prisoners:
                schedule_entries = self.schedule_repo.get_at_time(
                    day_of_week, time_str, location_id=cell.id
                )
                # Check if prisoner is scheduled to be in their cell
                prisoner_scheduled_here = any(
                    e.inmate_id == prisoner.id for e in schedule_entries
                )
                # Also count if it's their home cell and they're not scheduled elsewhere
                if prisoner_scheduled_here or self._is_prisoner_at_home(
                    prisoner.id, cell.id, day_of_week, time_str
                ):
                    expected_count += 1
            
            location_prisoner_counts[cell.id] = expected_count

        # Filter locations if not including empty
        cells_to_visit = all_cells
        if not include_empty:
            cells_to_visit = [
                c for c in all_cells if location_prisoner_counts.get(c.id, 0) > 0
            ]

        # Calculate optimal route
        cell_ids_to_visit = [c.id for c in cells_to_visit]
        optimized_route = self.pathfinding_service.calculate_route(cell_ids_to_visit)

        # Build route stops with counts
        route_stops: list[RouteStopInfo] = []
        for stop in optimized_route.stops:
            cell = next((c for c in all_cells if c.id == stop.location_id), None)
            expected_count = location_prisoner_counts.get(stop.location_id, 0)
            
            walking_distance = 0
            walking_time = 0
            if stop.walking_from_previous:
                walking_distance = stop.walking_from_previous.distance_meters
                walking_time = stop.walking_from_previous.time_seconds

            route_stops.append(RouteStopInfo(
                order=stop.order,
                location_id=stop.location_id,
                location_name=stop.location_name,
                location_type=cell.type.value if cell else "unknown",
                building=stop.building,
                floor=stop.floor,
                is_occupied=expected_count > 0,
                expected_count=expected_count,
                walking_distance_meters=walking_distance,
                walking_time_seconds=walking_time,
            ))

        # Calculate summary stats
        total_locations = len(all_cells)
        occupied_locations = sum(1 for c in all_cells if location_prisoner_counts.get(c.id, 0) > 0)
        empty_locations = total_locations - occupied_locations
        total_prisoners = sum(location_prisoner_counts.values())
        
        # Estimate verification time (30 seconds per prisoner + walking)
        verification_time = total_prisoners * 30
        estimated_time = optimized_route.total_time_seconds + verification_time

        # Get location names for all input locations
        location_names = []
        for loc_id in input_location_ids:
            loc = self.location_repo.get_by_id(loc_id)
            if loc:
                location_names.append(loc.name)

        return GeneratedRollCall(
            location_ids=input_location_ids,
            location_names=location_names,
            scheduled_at=scheduled_at,
            route=route_stops,
            total_locations=total_locations,
            occupied_locations=occupied_locations,
            empty_locations=empty_locations,
            total_prisoners_expected=total_prisoners,
            estimated_time_seconds=estimated_time,
        )

    def _get_descendant_location_ids(self, location_id: str) -> list[str]:
        """
        Get all descendant location IDs including the location itself.

        Traverses the location hierarchy to find all child locations.
        Useful for hierarchical queries (e.g., find all cells in a wing).

        Args:
            location_id: The parent location ID

        Returns:
            List of location IDs including the parent and all descendants
        """
        # Fetch all locations once for efficient traversal
        all_locations = self.location_repo.get_all()

        # Build a parent_id -> children map
        children_map: dict[str, list[str]] = {}
        for loc in all_locations:
            if loc.parent_id:
                if loc.parent_id not in children_map:
                    children_map[loc.parent_id] = []
                children_map[loc.parent_id].append(loc.id)

        # Breadth-first search to find all descendants
        descendants = [location_id]
        queue = [location_id]

        while queue:
            current_id = queue.pop(0)
            children = children_map.get(current_id, [])

            for child_id in children:
                descendants.append(child_id)
                queue.append(child_id)

        return descendants

    def _is_prisoner_at_home(
        self, inmate_id: str, home_cell_id: str, day_of_week: int, time_str: str
    ) -> bool:
        """
        Check if prisoner should be at home cell (not scheduled elsewhere).

        Args:
            inmate_id: The prisoner's ID
            home_cell_id: Their home cell ID
            day_of_week: Day of week (0-6)
            time_str: Time in HH:MM format

        Returns:
            True if prisoner should be at home cell
        """
        # Get all schedule entries for this prisoner at this time
        all_entries = self.schedule_repo.get_at_time(day_of_week, time_str)
        prisoner_entries = [e for e in all_entries if e.inmate_id == inmate_id]
        
        if not prisoner_entries:
            # No schedule = assume at home cell
            return True
        
        # Check if any entry is for a different location
        for entry in prisoner_entries:
            if entry.location_id != home_cell_id:
                return False
        
        return True

    def get_expected_prisoners(
        self,
        location_id: str,
        at_time: datetime,
    ) -> list[ExpectedPrisoner]:
        """
        Get list of prisoners expected at a location with priority info.

        Supports hierarchical locations - querying a wing returns all prisoners
        in cells within that wing.

        Args:
            location_id: The location to check
            at_time: The time to check

        Returns:
            List of expected prisoners sorted by priority (highest first)
        """
        day_of_week = at_time.weekday()
        time_str = at_time.strftime("%H:%M")

        expected_prisoners: list[ExpectedPrisoner] = []

        # Get all descendant location IDs (for hierarchical queries)
        descendant_ids = self._get_descendant_location_ids(location_id)

        # Get prisoners from all descendant locations
        home_cell_prisoners = []
        for loc_id in descendant_ids:
            home_cell_prisoners.extend(self.inmate_repo.get_by_home_cell(loc_id))
        
        for prisoner in home_cell_prisoners:
            # Check if they're supposed to be here
            if not self._is_prisoner_at_home(prisoner.id, location_id, day_of_week, time_str):
                continue  # Scheduled elsewhere
            
            # Get their schedule entries for today
            all_entries = self.schedule_repo.get_by_inmate(prisoner.id)
            today_entries = [e for e in all_entries if e.day_of_week == day_of_week]
            
            # Find current activity
            current_activity = "unknown"
            current_entries = [
                e for e in today_entries
                if e.start_time <= time_str < e.end_time
            ]
            if current_entries:
                current_activity = current_entries[0].activity_type.value
            
            # Find next appointment
            next_apt = self._get_next_appointment(
                prisoner.id, today_entries, time_str, at_time
            )
            
            # Calculate priority
            priority = self._calculate_priority(next_apt)
            
            expected_prisoners.append(ExpectedPrisoner(
                inmate=prisoner,
                home_cell_id=prisoner.home_cell_id,
                is_at_home_cell=True,
                current_activity=current_activity,
                next_appointment=next_apt,
                priority_score=priority,
            ))
        
        # Sort by priority (highest first)
        expected_prisoners.sort(key=lambda p: p.priority_score, reverse=True)

        return expected_prisoners

    def get_batch_expected_counts(
        self,
        location_ids: list[str],
        at_time: datetime,
    ) -> dict[str, int]:
        """
        Get expected prisoner counts for multiple locations efficiently.

        Optimized approach: Load all schedules active at the specified time
        to determine who is NOT at home, then count remaining prisoners.

        Args:
            location_ids: List of location IDs to query
            at_time: Time to check expected counts

        Returns:
            Dictionary mapping location_id to expected count
        """
        day_of_week = at_time.weekday()
        time_str = at_time.strftime("%H:%M")

        # Pre-fetch all data we'll need
        all_locations = self.location_repo.get_all()
        all_inmates = self.inmate_repo.get_all()

        # Build location hierarchy map for efficient lookups
        children_map: dict[str, list[str]] = {}
        for loc in all_locations:
            if loc.parent_id:
                if loc.parent_id not in children_map:
                    children_map[loc.parent_id] = []
                children_map[loc.parent_id].append(loc.id)

        # Build home_cell_id -> inmates map
        inmates_by_cell: dict[str, list] = {}
        for inmate in all_inmates:
            if inmate.home_cell_id:
                if inmate.home_cell_id not in inmates_by_cell:
                    inmates_by_cell[inmate.home_cell_id] = []
                inmates_by_cell[inmate.home_cell_id].append(inmate)

        # OPTIMIZATION: Get all schedules active at this time in ONE query
        # This tells us who is NOT at their home cell
        active_schedules = self.schedule_repo.get_at_time(day_of_week, time_str)

        # Build set of inmates who are scheduled elsewhere (NOT at home)
        inmates_not_at_home = {entry.inmate_id for entry in active_schedules}

        # Calculate counts for each location
        counts: dict[str, int] = {}

        for location_id in location_ids:
            # Get descendant location IDs using cached hierarchy
            descendant_ids = self._get_descendant_ids_cached(
                location_id, children_map
            )

            # Get prisoners from descendant cells
            home_cell_prisoners = []
            for loc_id in descendant_ids:
                home_cell_prisoners.extend(inmates_by_cell.get(loc_id, []))

            # Count prisoners who should be at this location
            # (those NOT in the scheduled-elsewhere set)
            count = sum(
                1 for prisoner in home_cell_prisoners
                if prisoner.id not in inmates_not_at_home
            )

            counts[location_id] = count

        return counts

    def _get_descendant_ids_cached(
        self, location_id: str, children_map: dict[str, list[str]]
    ) -> list[str]:
        """Get descendant location IDs using cached hierarchy map."""
        descendants = [location_id]
        queue = [location_id]

        while queue:
            current_id = queue.pop(0)
            children = children_map.get(current_id, [])

            for child_id in children:
                descendants.append(child_id)
                queue.append(child_id)

        return descendants

    def _get_next_appointment(
        self,
        inmate_id: str,
        today_entries: list[ScheduleEntry],
        current_time_str: str,
        current_datetime: datetime,
    ) -> Optional[NextAppointment]:
        """Get the next scheduled appointment for a prisoner."""
        # Find entries starting after current time
        future_entries = [
            e for e in today_entries
            if e.start_time > current_time_str
            and e.location_id != e.inmate_id  # Not staying in cell
        ]
        
        if not future_entries:
            return None
        
        # Sort by start time and get the next one
        future_entries.sort(key=lambda e: e.start_time)
        next_entry = future_entries[0]
        
        # Get location name
        location = self.location_repo.get_by_id(next_entry.location_id)
        location_name = location.name if location else "Unknown"
        
        # Calculate minutes until
        start_hour, start_min = map(int, next_entry.start_time.split(":"))
        start_dt = current_datetime.replace(hour=start_hour, minute=start_min, second=0)
        minutes_until = int((start_dt - current_datetime).total_seconds() / 60)
        
        return NextAppointment(
            activity_type=next_entry.activity_type.value,
            location_id=next_entry.location_id,
            location_name=location_name,
            start_time=next_entry.start_time,
            minutes_until=max(0, minutes_until),
            is_urgent=minutes_until < 30,
        )

    def _calculate_priority(self, next_apt: Optional[NextAppointment]) -> int:
        """
        Calculate priority score for verification order.
        
        Higher score = verify sooner.
        """
        score = 50  # Base score
        
        if next_apt:
            minutes_until = next_apt.minutes_until
            
            if minutes_until < 15:
                score += 50  # Very urgent
            elif minutes_until < 30:
                score += 40  # Urgent
            elif minutes_until < 60:
                score += 20  # Soon
            
            # Healthcare appointments get extra priority
            if next_apt.activity_type == "healthcare":
                score += 10
            
            # Visits (family) get priority too  
            if next_apt.activity_type == "visits":
                score += 5
        
        return min(score, 100)
