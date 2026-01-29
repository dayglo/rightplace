"""
Unit tests for schedule repository.

Tests CRUD operations for schedule entries with real SQLite database.
"""
from datetime import date, datetime

import pytest
import sqlite3

from app.db.database import get_connection, init_db
from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.models.inmate import InmateCreate
from app.models.location import Location, LocationType, LocationCreate
from app.models.schedule import (
    ActivityType,
    ScheduleEntry,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
)


@pytest.fixture
def db_conn(test_db):
    """Provide database connection for tests."""
    conn = get_connection(test_db)
    yield conn
    conn.close()


@pytest.fixture
def schedule_repo(db_conn):
    """Provide ScheduleRepository with test database."""
    return ScheduleRepository(db_conn)


@pytest.fixture
def inmate_repo(db_conn):
    """Provide InmateRepository for creating test inmates."""
    return InmateRepository(db_conn)


@pytest.fixture
def location_repo(db_conn):
    """Provide LocationRepository for creating test locations."""
    return LocationRepository(db_conn)


@pytest.fixture
def sample_inmate(inmate_repo):
    """Create a test inmate for FK relationships."""
    inmate_data = InmateCreate(
        inmate_number="A12345",
        first_name="John",
        last_name="Doe",
        date_of_birth=date(1990, 1, 15),
        cell_block="A",
        cell_number="101",
    )
    return inmate_repo.create(inmate_data)


@pytest.fixture
def sample_location(location_repo):
    """Create a test location for FK relationships."""
    location_data = LocationCreate(
        name="Workshop A",
        type=LocationType.WORKSHOP,
        building="Main Block",
        floor=1,
        capacity=20,
    )
    return location_repo.create(location_data)


@pytest.fixture
def sample_cell(location_repo):
    """Create a test cell location."""
    cell_data = LocationCreate(
        name="Cell A-101",
        type=LocationType.CELL,
        building="A Wing",
        floor=1,
        capacity=2,
    )
    return location_repo.create(cell_data)


class TestScheduleRepositoryCreate:
    """Tests for creating schedule entries."""

    def test_create_schedule_entry(self, schedule_repo, sample_inmate, sample_location):
        """Should create entry and return with generated ID."""
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,  # Tuesday
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )

        result = schedule_repo.create(entry_data)

        assert result.id is not None
        assert result.inmate_id == sample_inmate.id
        assert result.location_id == sample_location.id
        assert result.day_of_week == 1
        assert result.start_time == "09:00"
        assert result.end_time == "12:00"
        assert result.activity_type == ActivityType.WORK
        assert result.is_recurring is True  # Default
        assert result.source == "manual"  # Default
        assert result.created_at is not None
        assert result.updated_at is not None

    def test_create_with_custom_source(self, schedule_repo, sample_inmate, sample_location):
        """Should accept custom source parameter."""
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=2,
            start_time="10:00",
            end_time="11:00",
            activity_type=ActivityType.EDUCATION,
        )

        result = schedule_repo.create(entry_data, source="sync")

        assert result.source == "sync"

    def test_create_non_recurring_with_effective_date(
        self, schedule_repo, sample_inmate, sample_location
    ):
        """Should create one-off appointment with effective date."""
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=3,
            start_time="14:00",
            end_time="14:30",
            activity_type=ActivityType.HEALTHCARE,
            is_recurring=False,
            effective_date=date(2025, 2, 5),
        )

        result = schedule_repo.create(entry_data)

        assert result.is_recurring is False
        assert result.effective_date == date(2025, 2, 5)


class TestScheduleRepositoryRead:
    """Tests for reading schedule entries."""

    def test_get_by_id_found(self, schedule_repo, sample_inmate, sample_location):
        """Should retrieve entry by ID."""
        # Create entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=0,
            start_time="08:00",
            end_time="09:00",
            activity_type=ActivityType.MEAL,
        )
        created = schedule_repo.create(entry_data)

        # Retrieve by ID
        result = schedule_repo.get_by_id(created.id)

        assert result is not None
        assert result.id == created.id
        assert result.inmate_id == sample_inmate.id
        assert result.activity_type == ActivityType.MEAL

    def test_get_by_id_not_found(self, schedule_repo):
        """Should return None for unknown ID."""
        result = schedule_repo.get_by_id("nonexistent-id-123")
        assert result is None

    def test_get_by_inmate(self, schedule_repo, sample_inmate, sample_location):
        """Should get all entries for inmate sorted by day/time."""
        # Create multiple entries for the same inmate
        entries = [
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="14:00",
                end_time="15:00",
                activity_type=ActivityType.GYM,
            ),
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=0,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            ),
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="09:00",
                end_time="10:00",
                activity_type=ActivityType.EDUCATION,
            ),
        ]
        for entry in entries:
            schedule_repo.create(entry)

        # Get all entries for inmate
        results = schedule_repo.get_by_inmate(sample_inmate.id)

        assert len(results) == 3
        # Should be sorted by day_of_week, then start_time
        assert results[0].day_of_week == 0
        assert results[0].start_time == "09:00"
        assert results[1].day_of_week == 1
        assert results[1].start_time == "09:00"  # Education first (same day)
        assert results[2].day_of_week == 1
        assert results[2].start_time == "14:00"  # Gym later

    def test_get_by_location(self, schedule_repo, sample_inmate, inmate_repo, sample_location):
        """Should get all entries for location."""
        # Create second inmate
        inmate2_data = InmateCreate(
            inmate_number="A12346",
            first_name="Jane",
            last_name="Smith",
            date_of_birth=date(1992, 3, 20),
            cell_block="A",
            cell_number="102",
        )
        inmate2 = inmate_repo.create(inmate2_data)

        # Create entries at same location for different inmates
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            )
        )
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=inmate2.id,
                location_id=sample_location.id,
                day_of_week=2,
                start_time="10:00",
                end_time="11:00",
                activity_type=ActivityType.WORK,
            )
        )

        results = schedule_repo.get_by_location(sample_location.id)

        assert len(results) == 2
        assert all(r.location_id == sample_location.id for r in results)

    def test_get_by_location_with_day_filter(
        self, schedule_repo, sample_inmate, sample_location
    ):
        """Should filter by day_of_week when provided."""
        # Create entries on different days
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            )
        )
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=2,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            )
        )

        # Filter by day
        results = schedule_repo.get_by_location(sample_location.id, day_of_week=1)

        assert len(results) == 1
        assert results[0].day_of_week == 1

    def test_get_at_time_matches_active_entries(
        self, schedule_repo, sample_inmate, sample_location
    ):
        """Should find entries where start <= time < end."""
        # Create entries at different times
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            )
        )
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="14:00",
                end_time="16:00",
                activity_type=ActivityType.EDUCATION,
            )
        )

        # Check at 10:00 - should match first entry
        results = schedule_repo.get_at_time(day_of_week=1, time="10:00")

        assert len(results) == 1
        assert results[0].start_time == "09:00"
        assert results[0].end_time == "12:00"

        # Check at 15:00 - should match second entry
        results = schedule_repo.get_at_time(day_of_week=1, time="15:00")

        assert len(results) == 1
        assert results[0].start_time == "14:00"

    def test_get_at_time_excludes_wrong_day(
        self, schedule_repo, sample_inmate, sample_location
    ):
        """Should not match entries on different day."""
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            )
        )

        # Check different day
        results = schedule_repo.get_at_time(day_of_week=2, time="10:00")

        assert len(results) == 0

    def test_get_at_time_with_location_filter(
        self, schedule_repo, sample_inmate, sample_location, location_repo
    ):
        """Should combine time and location filters."""
        # Create second location
        location2_data = LocationCreate(
            name="Library",
            type=LocationType.EDUCATION,
            building="Main Block",
            floor=2,
            capacity=30,
        )
        location2 = location_repo.create(location2_data)

        # Create entries at different locations, same time
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            )
        )
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=location2.id,
                day_of_week=1,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.EDUCATION,
            )
        )

        # Filter by location
        results = schedule_repo.get_at_time(
            day_of_week=1, time="10:00", location_id=location2.id
        )

        assert len(results) == 1
        assert results[0].location_id == location2.id


class TestScheduleRepositoryUpdate:
    """Tests for updating schedule entries."""

    def test_update_schedule_entry(self, schedule_repo, sample_inmate, sample_location, location_repo):
        """Should update specified fields only."""
        # Create entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        created = schedule_repo.create(entry_data)

        # Create new location
        new_location_data = LocationCreate(
            name="Workshop B",
            type=LocationType.WORKSHOP,
            building="East Block",
            floor=1,
            capacity=15,
        )
        new_location = location_repo.create(new_location_data)

        # Update location and times
        update = ScheduleEntryUpdate(
            location_id=new_location.id,
            start_time="10:00",
            end_time="13:00",
        )
        result = schedule_repo.update(created.id, update)

        assert result is not None
        assert result.location_id == new_location.id
        assert result.start_time == "10:00"
        assert result.end_time == "13:00"
        # Unchanged fields
        assert result.inmate_id == sample_inmate.id
        assert result.day_of_week == 1
        assert result.activity_type == ActivityType.WORK

    def test_update_activity_type_only(self, schedule_repo, sample_inmate, sample_location):
        """Should allow updating just activity type."""
        # Create entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=2,
            start_time="14:00",
            end_time="15:00",
            activity_type=ActivityType.EXERCISE,
        )
        created = schedule_repo.create(entry_data)

        # Update only activity type
        update = ScheduleEntryUpdate(activity_type=ActivityType.GYM)
        result = schedule_repo.update(created.id, update)

        assert result.activity_type == ActivityType.GYM
        # Other fields unchanged
        assert result.start_time == "14:00"
        assert result.location_id == sample_location.id

    def test_update_nonexistent_entry(self, schedule_repo):
        """Should return None for unknown ID."""
        update = ScheduleEntryUpdate(start_time="10:00")
        result = schedule_repo.update("nonexistent-id", update)

        assert result is None

    def test_update_with_no_changes(self, schedule_repo, sample_inmate, sample_location):
        """Should return entry unchanged when update is empty."""
        # Create entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="10:00",
            activity_type=ActivityType.MEAL,
        )
        created = schedule_repo.create(entry_data)

        # Empty update
        update = ScheduleEntryUpdate()
        result = schedule_repo.update(created.id, update)

        assert result is not None
        assert result.id == created.id
        assert result.start_time == "09:00"


class TestScheduleRepositoryDelete:
    """Tests for deleting schedule entries."""

    def test_delete_schedule_entry(self, schedule_repo, sample_inmate, sample_location):
        """Should delete entry and return True."""
        # Create entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        created = schedule_repo.create(entry_data)

        # Delete
        result = schedule_repo.delete(created.id)

        assert result is True

        # Verify deleted
        found = schedule_repo.get_by_id(created.id)
        assert found is None

    def test_delete_nonexistent_entry(self, schedule_repo):
        """Should return False for unknown ID."""
        result = schedule_repo.delete("nonexistent-id")
        assert result is False

    def test_delete_by_source(self, schedule_repo, sample_inmate, sample_location):
        """Should delete all entries from specified source."""
        # Create entries with different sources
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=1,
                start_time="09:00",
                end_time="10:00",
                activity_type=ActivityType.WORK,
            ),
            source="manual",
        )
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=2,
                start_time="09:00",
                end_time="10:00",
                activity_type=ActivityType.WORK,
            ),
            source="sync",
        )
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=sample_inmate.id,
                location_id=sample_location.id,
                day_of_week=3,
                start_time="09:00",
                end_time="10:00",
                activity_type=ActivityType.WORK,
            ),
            source="sync",
        )

        # Delete all "sync" entries
        deleted_count = schedule_repo.delete_by_source("sync")

        assert deleted_count == 2

        # Verify manual entry still exists
        all_entries = schedule_repo.get_by_inmate(sample_inmate.id)
        assert len(all_entries) == 1
        assert all_entries[0].source == "manual"


class TestScheduleRepositoryPagination:
    """Tests for pagination and listing."""

    def test_list_all_with_pagination(self, schedule_repo, sample_inmate, sample_location):
        """Should paginate results with limit and offset."""
        # Create 10 entries
        for day in range(5):
            for hour in ["09:00", "14:00"]:
                schedule_repo.create(
                    ScheduleEntryCreate(
                        inmate_id=sample_inmate.id,
                        location_id=sample_location.id,
                        day_of_week=day,
                        start_time=hour,
                        end_time="10:00" if hour == "09:00" else "15:00",
                        activity_type=ActivityType.WORK,
                    )
                )

        # Get first page (5 entries)
        page1 = schedule_repo.list_all(limit=5, offset=0)
        assert len(page1) == 5

        # Get second page
        page2 = schedule_repo.list_all(limit=5, offset=5)
        assert len(page2) == 5

        # No overlap
        page1_ids = {e.id for e in page1}
        page2_ids = {e.id for e in page2}
        assert len(page1_ids & page2_ids) == 0

    def test_count(self, schedule_repo, sample_inmate, sample_location):
        """Should count total entries."""
        # Initially empty
        assert schedule_repo.count() == 0

        # Create entries
        for i in range(7):
            schedule_repo.create(
                ScheduleEntryCreate(
                    inmate_id=sample_inmate.id,
                    location_id=sample_location.id,
                    day_of_week=i % 7,
                    start_time="09:00",
                    end_time="10:00",
                    activity_type=ActivityType.WORK,
                )
            )

        assert schedule_repo.count() == 7


class TestScheduleRepositoryForeignKeys:
    """Tests for foreign key constraints."""

    def test_foreign_key_constraint_inmate(
        self, schedule_repo, sample_inmate, sample_location, inmate_repo
    ):
        """Should cascade delete when inmate is deleted."""
        # Create schedule entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        created = schedule_repo.create(entry_data)

        # Delete inmate
        inmate_repo.delete(sample_inmate.id)

        # Schedule entry should be cascade deleted
        result = schedule_repo.get_by_id(created.id)
        assert result is None

    def test_foreign_key_constraint_location(
        self, schedule_repo, sample_inmate, sample_location, location_repo
    ):
        """Should cascade delete when location is deleted."""
        # Create schedule entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        created = schedule_repo.create(entry_data)

        # Delete location
        location_repo.delete(sample_location.id)

        # Schedule entry should be cascade deleted
        result = schedule_repo.get_by_id(created.id)
        assert result is None

    def test_cannot_create_with_invalid_inmate(self, schedule_repo, sample_location):
        """Should fail to create entry with nonexistent inmate."""
        entry_data = ScheduleEntryCreate(
            inmate_id="nonexistent-inmate-id",
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )

        with pytest.raises(sqlite3.IntegrityError):
            schedule_repo.create(entry_data)

    def test_cannot_create_with_invalid_location(self, schedule_repo, sample_inmate):
        """Should fail to create entry with nonexistent location."""
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id="nonexistent-location-id",
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )

        with pytest.raises(sqlite3.IntegrityError):
            schedule_repo.create(entry_data)
