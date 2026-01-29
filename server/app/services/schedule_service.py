"""
Schedule service for business logic.

Handles schedule entry management with validation and conflict detection.
"""
from typing import Optional

from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.models.schedule import (
    ScheduleEntry,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
)


class ScheduleService:
    """Service for schedule entry business logic."""

    def __init__(
        self,
        schedule_repo: ScheduleRepository,
        inmate_repo: InmateRepository,
        location_repo: LocationRepository,
    ):
        """
        Initialize service with repositories.

        Args:
            schedule_repo: Schedule entry repository
            inmate_repo: Inmate repository
            location_repo: Location repository
        """
        self.schedule_repo = schedule_repo
        self.inmate_repo = inmate_repo
        self.location_repo = location_repo

    def create_schedule_entry(self, entry: ScheduleEntryCreate) -> ScheduleEntry:
        """
        Create schedule entry with validation.

        Args:
            entry: Schedule entry data

        Returns:
            Created schedule entry

        Raises:
            ValueError: If inmate/location not found or time conflict exists
        """
        # Validate inmate exists
        inmate = self.inmate_repo.get_by_id(entry.inmate_id)
        if not inmate:
            raise ValueError(f"Inmate {entry.inmate_id} not found")

        # Validate location exists
        location = self.location_repo.get_by_id(entry.location_id)
        if not location:
            raise ValueError(f"Location {entry.location_id} not found")

        # Check for conflicts
        conflicts = self._find_conflicts(
            inmate_id=entry.inmate_id,
            day=entry.day_of_week,
            start=entry.start_time,
            end=entry.end_time,
            exclude_id=None,
        )
        if conflicts:
            raise ValueError(
                f"Schedule conflict: inmate already scheduled "
                f"{conflicts[0].start_time}-{conflicts[0].end_time} "
                f"at {conflicts[0].location_id}"
            )

        return self.schedule_repo.create(entry)

    def get_inmate_schedule(self, inmate_id: str) -> list[ScheduleEntry]:
        """
        Get full week schedule for an inmate.

        Args:
            inmate_id: Inmate ID

        Returns:
            List of schedule entries sorted by day/time
        """
        return self.schedule_repo.get_by_inmate(inmate_id)

    def get_location_schedule(
        self, location_id: str, day_of_week: Optional[int] = None
    ) -> list[ScheduleEntry]:
        """
        Get all scheduled activities at a location.

        Args:
            location_id: Location ID
            day_of_week: Optional day filter (0-6)

        Returns:
            List of schedule entries for the location
        """
        return self.schedule_repo.get_by_location(location_id, day_of_week)

    def update_schedule_entry(
        self, entry_id: str, update: ScheduleEntryUpdate
    ) -> ScheduleEntry:
        """
        Update schedule entry with conflict validation.

        Args:
            entry_id: Schedule entry ID
            update: Fields to update

        Returns:
            Updated schedule entry

        Raises:
            ValueError: If entry not found or update creates conflict
        """
        # Check entry exists
        existing = self.schedule_repo.get_by_id(entry_id)
        if not existing:
            raise ValueError(f"Schedule entry {entry_id} not found")

        # Check for conflicts if times are being changed
        if update.start_time is not None or update.end_time is not None:
            # Use updated times if provided, otherwise use existing
            start_time = update.start_time if update.start_time else existing.start_time
            end_time = update.end_time if update.end_time else existing.end_time

            conflicts = self._find_conflicts(
                inmate_id=existing.inmate_id,
                day=existing.day_of_week,
                start=start_time,
                end=end_time,
                exclude_id=entry_id,  # Exclude self from conflict check
            )
            if conflicts:
                raise ValueError(
                    f"Schedule conflict: inmate already scheduled "
                    f"{conflicts[0].start_time}-{conflicts[0].end_time} "
                    f"at {conflicts[0].location_id}"
                )

        result = self.schedule_repo.update(entry_id, update)
        if not result:
            raise ValueError(f"Schedule entry {entry_id} not found")

        return result

    def delete_schedule_entry(self, entry_id: str) -> bool:
        """
        Delete a schedule entry.

        Args:
            entry_id: Schedule entry ID

        Returns:
            True if deleted, False if not found
        """
        return self.schedule_repo.delete(entry_id)

    def _find_conflicts(
        self,
        inmate_id: str,
        day: int,
        start: str,
        end: str,
        exclude_id: Optional[str],
    ) -> list[ScheduleEntry]:
        """
        Find overlapping schedule entries for an inmate.

        Args:
            inmate_id: Inmate ID
            day: Day of week (0-6)
            start: Start time (HH:MM)
            end: End time (HH:MM)
            exclude_id: Optional entry ID to exclude (for updates)

        Returns:
            List of conflicting schedule entries
        """
        # Get all entries for inmate on this day
        all_entries = self.schedule_repo.get_by_inmate(inmate_id)
        day_entries = [e for e in all_entries if e.day_of_week == day]

        # Filter out the entry being updated
        if exclude_id:
            day_entries = [e for e in day_entries if e.id != exclude_id]

        # Check for time overlaps
        # Times overlap if: new_start < existing_end AND new_end > existing_start
        conflicts = []
        for entry in day_entries:
            if start < entry.end_time and end > entry.start_time:
                conflicts.append(entry)

        return conflicts
