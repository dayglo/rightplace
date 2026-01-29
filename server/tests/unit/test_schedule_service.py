"""
Unit tests for schedule service.

Tests business logic for schedule management including conflict detection.
"""
from datetime import date

import pytest

from app.db.database import get_connection
from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.services.schedule_service import ScheduleService
from app.models.inmate import InmateCreate
from app.models.location import LocationCreate, LocationType
from app.models.schedule import (
    ActivityType,
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
    """Provide ScheduleRepository."""
    return ScheduleRepository(db_conn)


@pytest.fixture
def inmate_repo(db_conn):
    """Provide InmateRepository."""
    return InmateRepository(db_conn)


@pytest.fixture
def location_repo(db_conn):
    """Provide LocationRepository."""
    return LocationRepository(db_conn)


@pytest.fixture
def schedule_service(schedule_repo, inmate_repo, location_repo):
    """Provide ScheduleService with all dependencies."""
    return ScheduleService(
        schedule_repo=schedule_repo,
        inmate_repo=inmate_repo,
        location_repo=location_repo,
    )


@pytest.fixture
def sample_inmate(inmate_repo):
    """Create a test inmate."""
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
    """Create a test location."""
    location_data = LocationCreate(
        name="Workshop A",
        type=LocationType.WORKSHOP,
        building="Main Block",
        floor=1,
        capacity=20,
    )
    return location_repo.create(location_data)


class TestScheduleServiceCreate:
    """Tests for creating schedule entries."""

    def test_create_schedule_entry_success(
        self, schedule_service, sample_inmate, sample_location
    ):
        """Should create entry when no conflicts exist."""
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )

        result = schedule_service.create_schedule_entry(entry_data)

        assert result.id is not None
        assert result.inmate_id == sample_inmate.id
        assert result.location_id == sample_location.id
        assert result.day_of_week == 1
        assert result.activity_type == ActivityType.WORK

    def test_create_schedule_entry_validates_inmate_exists(
        self, schedule_service, sample_location
    ):
        """Should raise ValueError for unknown inmate."""
        entry_data = ScheduleEntryCreate(
            inmate_id="nonexistent-inmate-id",
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )

        with pytest.raises(ValueError) as exc:
            schedule_service.create_schedule_entry(entry_data)

        assert "Inmate" in str(exc.value)
        assert "not found" in str(exc.value)

    def test_create_schedule_entry_validates_location_exists(
        self, schedule_service, sample_inmate
    ):
        """Should raise ValueError for unknown location."""
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id="nonexistent-location-id",
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )

        with pytest.raises(ValueError) as exc:
            schedule_service.create_schedule_entry(entry_data)

        assert "Location" in str(exc.value)
        assert "not found" in str(exc.value)

    def test_create_detects_time_conflict(
        self, schedule_service, sample_inmate, sample_location
    ):
        """Should raise ValueError when inmate has overlapping entry."""
        # Create first entry
        entry1 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        schedule_service.create_schedule_entry(entry1)

        # Try to create overlapping entry (same day, overlapping time)
        entry2 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="10:00",  # Overlaps with 09:00-12:00
            end_time="13:00",
            activity_type=ActivityType.EDUCATION,
        )

        with pytest.raises(ValueError) as exc:
            schedule_service.create_schedule_entry(entry2)

        assert "conflict" in str(exc.value).lower()

    def test_create_allows_different_days_same_time(
        self, schedule_service, sample_inmate, sample_location
    ):
        """Should allow same time on different days."""
        # Create entry on Monday
        entry1 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=0,  # Monday
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        schedule_service.create_schedule_entry(entry1)

        # Create entry on Tuesday (same time, no conflict)
        entry2 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,  # Tuesday
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        result = schedule_service.create_schedule_entry(entry2)

        assert result is not None
        assert result.day_of_week == 1

    def test_create_allows_same_location_different_times(
        self, schedule_service, sample_inmate, sample_location
    ):
        """Should allow same location at different times."""
        # Create morning entry
        entry1 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        schedule_service.create_schedule_entry(entry1)

        # Create afternoon entry (same day, no time overlap)
        entry2 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="14:00",
            end_time="16:00",
            activity_type=ActivityType.WORK,
        )
        result = schedule_service.create_schedule_entry(entry2)

        assert result is not None
        assert result.start_time == "14:00"

    def test_create_detects_exact_time_overlap(
        self, schedule_service, sample_inmate, sample_location
    ):
        """Should detect conflict when times exactly overlap."""
        # Create first entry
        entry1 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=2,
            start_time="10:00",
            end_time="11:00",
            activity_type=ActivityType.GYM,
        )
        schedule_service.create_schedule_entry(entry1)

        # Try exact same time
        entry2 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=2,
            start_time="10:00",
            end_time="11:00",
            activity_type=ActivityType.EXERCISE,
        )

        with pytest.raises(ValueError) as exc:
            schedule_service.create_schedule_entry(entry2)

        assert "conflict" in str(exc.value).lower()

    def test_create_allows_adjacent_times(
        self, schedule_service, sample_inmate, sample_location
    ):
        """Should allow entries with adjacent times (no overlap)."""
        # Create first entry ending at 12:00
        entry1 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=3,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        schedule_service.create_schedule_entry(entry1)

        # Create entry starting at 12:00 (adjacent, no overlap)
        entry2 = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=3,
            start_time="12:00",
            end_time="13:00",
            activity_type=ActivityType.MEAL,
        )
        result = schedule_service.create_schedule_entry(entry2)

        assert result is not None


class TestScheduleServiceRead:
    """Tests for reading schedule entries."""

    def test_get_inmate_schedule(
        self, schedule_service, schedule_repo, sample_inmate, sample_location
    ):
        """Should return full week schedule for inmate."""
        # Create multiple entries
        for day in range(5):  # Monday-Friday
            schedule_repo.create(
                ScheduleEntryCreate(
                    inmate_id=sample_inmate.id,
                    location_id=sample_location.id,
                    day_of_week=day,
                    start_time="09:00",
                    end_time="12:00",
                    activity_type=ActivityType.WORK,
                )
            )

        result = schedule_service.get_inmate_schedule(sample_inmate.id)

        assert len(result) == 5
        assert all(e.inmate_id == sample_inmate.id for e in result)

    def test_get_location_schedule(
        self, schedule_service, schedule_repo, inmate_repo, sample_location
    ):
        """Should return all activities at location."""
        # Create two inmates
        inmate1_data = InmateCreate(
            inmate_number="A11111",
            first_name="Alice",
            last_name="Smith",
            date_of_birth=date(1991, 5, 10),
            cell_block="A",
            cell_number="201",
        )
        inmate1 = inmate_repo.create(inmate1_data)

        inmate2_data = InmateCreate(
            inmate_number="A22222",
            first_name="Bob",
            last_name="Jones",
            date_of_birth=date(1992, 8, 22),
            cell_block="B",
            cell_number="102",
        )
        inmate2 = inmate_repo.create(inmate2_data)

        # Create entries for both inmates at same location
        schedule_repo.create(
            ScheduleEntryCreate(
                inmate_id=inmate1.id,
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
                day_of_week=1,
                start_time="14:00",
                end_time="16:00",
                activity_type=ActivityType.WORK,
            )
        )

        result = schedule_service.get_location_schedule(sample_location.id)

        assert len(result) == 2
        assert all(e.location_id == sample_location.id for e in result)

    def test_get_location_schedule_with_day_filter(
        self, schedule_service, schedule_repo, sample_inmate, sample_location
    ):
        """Should filter location schedule by day."""
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

        # Filter by day 1
        result = schedule_service.get_location_schedule(sample_location.id, day_of_week=1)

        assert len(result) == 1
        assert result[0].day_of_week == 1


class TestScheduleServiceUpdate:
    """Tests for updating schedule entries."""

    def test_update_schedule_entry_success(
        self, schedule_service, schedule_repo, sample_inmate, sample_location, location_repo
    ):
        """Should update entry when no new conflicts."""
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
            name="Library",
            type=LocationType.EDUCATION,
            building="East Block",
            floor=2,
            capacity=30,
        )
        new_location = location_repo.create(new_location_data)

        # Update to new location
        update = ScheduleEntryUpdate(location_id=new_location.id)
        result = schedule_service.update_schedule_entry(created.id, update)

        assert result is not None
        assert result.location_id == new_location.id

    def test_update_schedule_entry_detects_conflict(
        self, schedule_service, schedule_repo, sample_inmate, sample_location
    ):
        """Should prevent update that creates conflict."""
        # Create two non-conflicting entries
        entry1_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        entry1 = schedule_repo.create(entry1_data)

        entry2_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=1,
            start_time="14:00",
            end_time="16:00",
            activity_type=ActivityType.EDUCATION,
        )
        entry2 = schedule_repo.create(entry2_data)

        # Try to update entry2 to overlap with entry1
        update = ScheduleEntryUpdate(start_time="10:00", end_time="15:00")

        with pytest.raises(ValueError) as exc:
            schedule_service.update_schedule_entry(entry2.id, update)

        assert "conflict" in str(exc.value).lower()

    def test_update_schedule_entry_validates_entry_exists(self, schedule_service):
        """Should raise ValueError for unknown entry ID."""
        update = ScheduleEntryUpdate(start_time="10:00")

        with pytest.raises(ValueError) as exc:
            schedule_service.update_schedule_entry("nonexistent-id", update)

        assert "not found" in str(exc.value)

    def test_update_allows_self_overlap(
        self, schedule_service, schedule_repo, sample_inmate, sample_location
    ):
        """Should allow updating an entry to overlap with itself."""
        # Create entry
        entry_data = ScheduleEntryCreate(
            inmate_id=sample_inmate.id,
            location_id=sample_location.id,
            day_of_week=2,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        created = schedule_repo.create(entry_data)

        # Update to slightly different time (should not conflict with itself)
        update = ScheduleEntryUpdate(start_time="09:30", end_time="11:30")
        result = schedule_service.update_schedule_entry(created.id, update)

        assert result is not None
        assert result.start_time == "09:30"


class TestScheduleServiceDelete:
    """Tests for deleting schedule entries."""

    def test_delete_schedule_entry(
        self, schedule_service, schedule_repo, sample_inmate, sample_location
    ):
        """Should delete entry successfully."""
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
        result = schedule_service.delete_schedule_entry(created.id)

        assert result is True

        # Verify deleted
        found = schedule_repo.get_by_id(created.id)
        assert found is None

    def test_delete_nonexistent_entry(self, schedule_service):
        """Should return False for unknown entry ID."""
        result = schedule_service.delete_schedule_entry("nonexistent-id")
        assert result is False
