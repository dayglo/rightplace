"""
Unit tests for schedule data models.

Tests Pydantic validation for ScheduleEntry, ActivityType, and related models.
"""
from datetime import date, datetime

import pytest
from pydantic import ValidationError

from app.models.schedule import (
    ActivityType,
    ScheduleEntry,
    ScheduleEntryCreate,
    ScheduleEntryUpdate,
    ScheduleQuery,
    ScheduleSyncBatch,
)


class TestActivityType:
    """Tests for ActivityType enum."""

    def test_all_activity_types_defined(self):
        """Should have 23 activity types defined."""
        expected_types = {
            # Base regime
            "roll_check",
            "lock_up",
            "unlock",
            "meal",
            "association",
            "exercise",
            # Work and education
            "work",
            "education",
            # Activities and programmes
            "gym",
            "chapel",
            "programmes",
            # Visits and appointments
            "visits",
            "healthcare",
            # Special unit activities
            "healthcare_residence",
            "medical_round",
            "induction",
            "reception_processing",
            # Admin appointments
            "intake_interview",
            "probation_meeting",
            "disciplinary_hearing",
            "psychology_session",
            "case_review",
        }
        actual_types = {t.value for t in ActivityType}
        assert actual_types == expected_types

    def test_activity_type_values(self):
        """Should have correct string values for common activities."""
        assert ActivityType.WORK.value == "work"
        assert ActivityType.HEALTHCARE.value == "healthcare"
        assert ActivityType.VISITS.value == "visits"
        assert ActivityType.MEAL.value == "meal"

    def test_activity_type_from_string(self):
        """Should create ActivityType from string value."""
        activity = ActivityType("work")
        assert activity == ActivityType.WORK


class TestScheduleEntry:
    """Tests for ScheduleEntry model."""

    def test_valid_schedule_entry(self):
        """Should create valid schedule entry with all required fields."""
        entry = ScheduleEntry(
            id="entry-123",
            inmate_id="inmate-456",
            location_id="loc-789",
            day_of_week=1,  # Tuesday
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert entry.id == "entry-123"
        assert entry.inmate_id == "inmate-456"
        assert entry.location_id == "loc-789"
        assert entry.day_of_week == 1
        assert entry.start_time == "09:00"
        assert entry.end_time == "12:00"
        assert entry.activity_type == ActivityType.WORK

    def test_schedule_entry_with_optional_fields(self):
        """Should create entry with optional fields set."""
        entry = ScheduleEntry(
            id="entry-123",
            inmate_id="inmate-456",
            location_id="loc-789",
            day_of_week=3,
            start_time="14:00",
            end_time="15:30",
            activity_type=ActivityType.HEALTHCARE,
            is_recurring=False,
            effective_date=date(2025, 1, 15),
            source="sync",
            source_id="ext-999",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert entry.is_recurring is False
        assert entry.effective_date == date(2025, 1, 15)
        assert entry.source == "sync"
        assert entry.source_id == "ext-999"

    def test_schedule_entry_default_values(self):
        """Should use default values for optional fields."""
        entry = ScheduleEntry(
            id="entry-123",
            inmate_id="inmate-456",
            location_id="loc-789",
            day_of_week=0,
            start_time="08:00",
            end_time="09:00",
            activity_type=ActivityType.MEAL,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert entry.is_recurring is True  # Default
        assert entry.effective_date is None
        assert entry.source == "manual"  # Default
        assert entry.source_id is None

    def test_time_format_validation(self):
        """Should enforce HH:MM time format."""
        # Valid format
        entry = ScheduleEntry(
            id="entry-123",
            inmate_id="inmate-456",
            location_id="loc-789",
            day_of_week=0,
            start_time="09:30",
            end_time="10:45",
            activity_type=ActivityType.EXERCISE,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert entry.start_time == "09:30"
        assert entry.end_time == "10:45"

        # Invalid format - missing leading zero
        with pytest.raises(ValidationError) as exc:
            ScheduleEntry(
                id="entry-123",
                inmate_id="inmate-456",
                location_id="loc-789",
                day_of_week=0,
                start_time="9:30",  # Should be "09:30"
                end_time="10:45",
                activity_type=ActivityType.EXERCISE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        assert "start_time" in str(exc.value)

        # Invalid format - wrong separator
        with pytest.raises(ValidationError) as exc:
            ScheduleEntry(
                id="entry-123",
                inmate_id="inmate-456",
                location_id="loc-789",
                day_of_week=0,
                start_time="09-30",  # Should use colon
                end_time="10:45",
                activity_type=ActivityType.EXERCISE,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        assert "start_time" in str(exc.value)

    def test_end_time_after_start_time_validation(self):
        """Should reject end_time before or equal to start_time."""
        # Valid - end after start
        entry = ScheduleEntry(
            id="entry-123",
            inmate_id="inmate-456",
            location_id="loc-789",
            day_of_week=0,
            start_time="09:00",
            end_time="10:00",
            activity_type=ActivityType.WORK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert entry.end_time > entry.start_time

        # Invalid - end equals start
        with pytest.raises(ValidationError) as exc:
            ScheduleEntry(
                id="entry-123",
                inmate_id="inmate-456",
                location_id="loc-789",
                day_of_week=0,
                start_time="09:00",
                end_time="09:00",  # Same as start
                activity_type=ActivityType.WORK,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        assert "end_time must be after start_time" in str(exc.value)

        # Invalid - end before start
        with pytest.raises(ValidationError) as exc:
            ScheduleEntry(
                id="entry-123",
                inmate_id="inmate-456",
                location_id="loc-789",
                day_of_week=0,
                start_time="10:00",
                end_time="09:00",  # Before start
                activity_type=ActivityType.WORK,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        assert "end_time must be after start_time" in str(exc.value)

    def test_day_of_week_range_validation(self):
        """Should enforce day_of_week range 0-6."""
        # Valid - Monday (0)
        entry = ScheduleEntry(
            id="entry-123",
            inmate_id="inmate-456",
            location_id="loc-789",
            day_of_week=0,
            start_time="09:00",
            end_time="10:00",
            activity_type=ActivityType.WORK,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert entry.day_of_week == 0

        # Valid - Sunday (6)
        entry = ScheduleEntry(
            id="entry-123",
            inmate_id="inmate-456",
            location_id="loc-789",
            day_of_week=6,
            start_time="09:00",
            end_time="10:00",
            activity_type=ActivityType.CHAPEL,
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        assert entry.day_of_week == 6

        # Invalid - negative
        with pytest.raises(ValidationError) as exc:
            ScheduleEntry(
                id="entry-123",
                inmate_id="inmate-456",
                location_id="loc-789",
                day_of_week=-1,
                start_time="09:00",
                end_time="10:00",
                activity_type=ActivityType.WORK,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        assert "day_of_week" in str(exc.value)

        # Invalid - greater than 6
        with pytest.raises(ValidationError) as exc:
            ScheduleEntry(
                id="entry-123",
                inmate_id="inmate-456",
                location_id="loc-789",
                day_of_week=7,
                start_time="09:00",
                end_time="10:00",
                activity_type=ActivityType.WORK,
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
        assert "day_of_week" in str(exc.value)


class TestScheduleEntryCreate:
    """Tests for ScheduleEntryCreate model."""

    def test_create_with_required_fields_only(self):
        """Should create with required fields only."""
        entry = ScheduleEntryCreate(
            inmate_id="inmate-123",
            location_id="loc-456",
            day_of_week=2,
            start_time="10:00",
            end_time="11:30",
            activity_type=ActivityType.EDUCATION,
        )
        assert entry.inmate_id == "inmate-123"
        assert entry.location_id == "loc-456"
        assert entry.day_of_week == 2
        assert entry.start_time == "10:00"
        assert entry.end_time == "11:30"
        assert entry.activity_type == ActivityType.EDUCATION
        # Check defaults
        assert entry.is_recurring is True
        assert entry.effective_date is None

    def test_create_with_optional_effective_date(self):
        """Should accept effective_date for one-off appointments."""
        entry = ScheduleEntryCreate(
            inmate_id="inmate-123",
            location_id="loc-456",
            day_of_week=3,
            start_time="14:00",
            end_time="14:30",
            activity_type=ActivityType.HEALTHCARE,
            is_recurring=False,
            effective_date=date(2025, 2, 5),
        )
        assert entry.is_recurring is False
        assert entry.effective_date == date(2025, 2, 5)

    def test_create_time_validation(self):
        """Should validate time format in create model."""
        # Valid
        entry = ScheduleEntryCreate(
            inmate_id="inmate-123",
            location_id="loc-456",
            day_of_week=1,
            start_time="08:30",
            end_time="09:45",
            activity_type=ActivityType.MEAL,
        )
        assert entry.start_time == "08:30"

        # Invalid format
        with pytest.raises(ValidationError):
            ScheduleEntryCreate(
                inmate_id="inmate-123",
                location_id="loc-456",
                day_of_week=1,
                start_time="8:30",  # Missing leading zero
                end_time="09:45",
                activity_type=ActivityType.MEAL,
            )

    def test_create_end_time_validation(self):
        """Should validate end_time after start_time in create model."""
        # Valid
        entry = ScheduleEntryCreate(
            inmate_id="inmate-123",
            location_id="loc-456",
            day_of_week=1,
            start_time="09:00",
            end_time="12:00",
            activity_type=ActivityType.WORK,
        )
        assert entry.end_time > entry.start_time

        # Invalid - end before start
        with pytest.raises(ValidationError) as exc:
            ScheduleEntryCreate(
                inmate_id="inmate-123",
                location_id="loc-456",
                day_of_week=1,
                start_time="12:00",
                end_time="09:00",
                activity_type=ActivityType.WORK,
            )
        assert "end_time must be after start_time" in str(exc.value)


class TestScheduleEntryUpdate:
    """Tests for ScheduleEntryUpdate model."""

    def test_all_fields_optional(self):
        """Should allow creating update with no fields set."""
        update = ScheduleEntryUpdate()
        assert update.location_id is None
        assert update.start_time is None
        assert update.end_time is None
        assert update.activity_type is None

    def test_partial_update_location_only(self):
        """Should allow updating just location."""
        update = ScheduleEntryUpdate(location_id="new-loc-789")
        assert update.location_id == "new-loc-789"
        assert update.start_time is None
        assert update.end_time is None

    def test_partial_update_times_only(self):
        """Should allow updating just times."""
        update = ScheduleEntryUpdate(
            start_time="10:00",
            end_time="11:00",
        )
        assert update.start_time == "10:00"
        assert update.end_time == "11:00"
        assert update.location_id is None

    def test_partial_update_activity_type(self):
        """Should allow updating just activity type."""
        update = ScheduleEntryUpdate(activity_type=ActivityType.GYM)
        assert update.activity_type == ActivityType.GYM

    def test_update_time_format_validation(self):
        """Should validate time format in update model."""
        # Valid
        update = ScheduleEntryUpdate(start_time="14:30")
        assert update.start_time == "14:30"

        # Invalid
        with pytest.raises(ValidationError):
            ScheduleEntryUpdate(start_time="2:30pm")


class TestScheduleQuery:
    """Tests for ScheduleQuery model."""

    def test_query_all_fields_optional(self):
        """Should create query with all fields optional."""
        query = ScheduleQuery()
        assert query.inmate_id is None
        assert query.location_id is None
        assert query.day_of_week is None
        assert query.time is None
        assert query.activity_type is None

    def test_query_by_inmate(self):
        """Should query by inmate ID."""
        query = ScheduleQuery(inmate_id="inmate-123")
        assert query.inmate_id == "inmate-123"

    def test_query_by_location_and_day(self):
        """Should query by location and day combination."""
        query = ScheduleQuery(location_id="loc-456", day_of_week=2)
        assert query.location_id == "loc-456"
        assert query.day_of_week == 2

    def test_query_by_time_and_activity(self):
        """Should query by time and activity type."""
        query = ScheduleQuery(time="09:00", activity_type=ActivityType.MEAL)
        assert query.time == "09:00"
        assert query.activity_type == ActivityType.MEAL


class TestScheduleSyncBatch:
    """Tests for ScheduleSyncBatch model."""

    def test_sync_batch_with_entries(self):
        """Should create sync batch with list of entries."""
        entries = [
            ScheduleEntryCreate(
                inmate_id="inmate-1",
                location_id="loc-1",
                day_of_week=0,
                start_time="09:00",
                end_time="12:00",
                activity_type=ActivityType.WORK,
            ),
            ScheduleEntryCreate(
                inmate_id="inmate-2",
                location_id="loc-2",
                day_of_week=1,
                start_time="14:00",
                end_time="15:00",
                activity_type=ActivityType.HEALTHCARE,
            ),
        ]
        batch = ScheduleSyncBatch(entries=entries)
        assert batch.source == "sync"
        assert len(batch.entries) == 2
        assert batch.entries[0].inmate_id == "inmate-1"
        assert batch.entries[1].activity_type == ActivityType.HEALTHCARE

    def test_sync_batch_default_source(self):
        """Should default source to 'sync'."""
        batch = ScheduleSyncBatch(entries=[])
        assert batch.source == "sync"

    def test_sync_batch_custom_source(self):
        """Should allow custom source."""
        batch = ScheduleSyncBatch(source="nomis", entries=[])
        assert batch.source == "nomis"
