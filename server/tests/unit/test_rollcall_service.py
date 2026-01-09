"""
Test suite for RollCallService.

Tests business logic for roll call management.
"""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.db.database import get_connection, init_db
from app.db.repositories.rollcall_repo import RollCallRepository
from app.db.repositories.verification_repo import VerificationRepository
from app.services.rollcall_service import RollCallService
from app.models.rollcall import RollCallCreate, RollCallStatus, RouteStop


@pytest.fixture
def db_conn():
    """Create an in-memory database connection for testing."""
    conn = get_connection(":memory:")
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def rollcall_repo(db_conn):
    """Create a RollCallRepository instance."""
    return RollCallRepository(db_conn)


@pytest.fixture
def verification_repo(db_conn):
    """Create a VerificationRepository instance."""
    return VerificationRepository(db_conn)


@pytest.fixture
def rollcall_service(rollcall_repo, verification_repo):
    """Create a RollCallService instance."""
    return RollCallService(rollcall_repo, verification_repo)


@pytest.fixture
def sample_route_stops():
    """Sample route stops for testing."""
    return [
        RouteStop(
            id="stop1",
            location_id="loc1",
            order=1,
            expected_inmates=["inmate1", "inmate2"],
            status="pending",
        ),
        RouteStop(
            id="stop2",
            location_id="loc2",
            order=2,
            expected_inmates=["inmate3"],
            status="pending",
        ),
    ]


@pytest.fixture
def sample_rollcall_data(sample_route_stops):
    """Sample roll call data for testing."""
    return RollCallCreate(
        name="Morning Roll Call",
        scheduled_at=datetime.now() + timedelta(hours=1),
        route=sample_route_stops,
        officer_id="officer1",
        notes="Test roll call",
    )


class TestRollCallServiceCreate:
    """Test roll call creation logic."""

    def test_create_rollcall_success(self, rollcall_service, sample_rollcall_data):
        """Should create roll call with scheduled status."""
        rollcall = rollcall_service.create_roll_call(sample_rollcall_data)

        assert rollcall.id is not None
        assert rollcall.status == RollCallStatus.SCHEDULED
        assert rollcall.name == "Morning Roll Call"

    def test_create_rollcall_validates_route_not_empty(self, rollcall_service):
        """Should raise error when route is empty."""
        with pytest.raises(ValueError, match="Route cannot be empty"):
            rollcall_service.create_roll_call(
                RollCallCreate(
                    name="Empty Route Roll Call",
                    scheduled_at=datetime.now(),
                    route=[],
                    officer_id="officer1",
                )
            )

    def test_create_rollcall_validates_scheduled_time(
        self, rollcall_service, sample_route_stops
    ):
        """Should raise error when scheduled time is in the past."""
        with pytest.raises(ValueError, match="Scheduled time cannot be in the past"):
            rollcall_service.create_roll_call(
                RollCallCreate(
                    name="Past Roll Call",
                    scheduled_at=datetime.now() - timedelta(hours=1),
                    route=sample_route_stops,
                    officer_id="officer1",
                )
            )


class TestRollCallServiceStatusTransitions:
    """Test roll call status transition logic."""

    def test_start_rollcall_success(self, rollcall_service, sample_rollcall_data):
        """Should transition roll call to in_progress."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)

        started = rollcall_service.start_roll_call(created.id)

        assert started.status == RollCallStatus.IN_PROGRESS
        assert started.started_at is not None

    def test_start_rollcall_not_found(self, rollcall_service):
        """Should raise error when roll call not found."""
        with pytest.raises(ValueError, match="Roll call .* not found"):
            rollcall_service.start_roll_call("non-existent-id")

    def test_start_rollcall_already_started(
        self, rollcall_service, sample_rollcall_data
    ):
        """Should raise error when roll call already in progress."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)

        with pytest.raises(ValueError, match="already in progress"):
            rollcall_service.start_roll_call(created.id)

    def test_complete_rollcall_success(self, rollcall_service, sample_rollcall_data):
        """Should transition roll call to completed."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)

        completed = rollcall_service.complete_roll_call(created.id)

        assert completed.status == RollCallStatus.COMPLETED
        assert completed.completed_at is not None

    def test_complete_rollcall_not_started(
        self, rollcall_service, sample_rollcall_data
    ):
        """Should raise error when completing non-started roll call."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)

        with pytest.raises(ValueError, match="not in progress"):
            rollcall_service.complete_roll_call(created.id)

    def test_cancel_rollcall_success(self, rollcall_service, sample_rollcall_data):
        """Should cancel roll call with reason."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)

        cancelled = rollcall_service.cancel_roll_call(
            created.id, "Emergency situation"
        )

        assert cancelled.status == RollCallStatus.CANCELLED
        assert cancelled.cancelled_reason == "Emergency situation"

    def test_cancel_rollcall_requires_reason(
        self, rollcall_service, sample_rollcall_data
    ):
        """Should raise error when cancel reason not provided."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)

        with pytest.raises(ValueError, match="Cancellation reason required"):
            rollcall_service.cancel_roll_call(created.id, "")


class TestRollCallServiceRouteManagement:
    """Test route stop management logic."""

    def test_get_current_stop(self, rollcall_service, sample_rollcall_data):
        """Should return current stop in route."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)

        current_stop = rollcall_service.get_current_stop(created.id)

        assert current_stop is not None
        assert current_stop.id == "stop1"
        assert current_stop.status == "pending"

    def test_advance_to_next_stop(self, rollcall_service, sample_rollcall_data):
        """Should advance to next stop in route."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)

        rollcall_service.complete_current_stop(created.id)
        current_stop = rollcall_service.get_current_stop(created.id)

        assert current_stop is not None
        assert current_stop.id == "stop2"

    def test_complete_stop_updates_status(
        self, rollcall_service, sample_rollcall_data
    ):
        """Should mark stop as completed."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)

        updated = rollcall_service.complete_current_stop(created.id)

        assert updated.route[0].status == "completed"
        assert updated.route[0].completed_at is not None

    def test_skip_stop_with_reason(self, rollcall_service, sample_rollcall_data):
        """Should skip stop with reason."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)

        updated = rollcall_service.skip_current_stop(
            created.id, "Location inaccessible"
        )

        assert updated.route[0].status == "skipped"
        assert updated.route[0].skip_reason == "Location inaccessible"


class TestRollCallServiceStatistics:
    """Test roll call statistics logic."""

    def test_get_progress_stats(self, rollcall_service, sample_rollcall_data):
        """Should calculate progress statistics."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)

        stats = rollcall_service.get_progress_stats(created.id)

        assert stats["total_stops"] == 2
        assert stats["completed_stops"] == 0
        assert stats["skipped_stops"] == 0
        assert stats["expected_inmates"] == 3  # 2 + 1
        assert stats["verified_inmates"] == 0

    def test_progress_stats_with_completed_stops(
        self, rollcall_service, sample_rollcall_data
    ):
        """Should count completed stops."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)
        rollcall_service.complete_current_stop(created.id)

        stats = rollcall_service.get_progress_stats(created.id)

        assert stats["completed_stops"] == 1

    def test_progress_percentage(self, rollcall_service, sample_rollcall_data):
        """Should calculate progress percentage."""
        created = rollcall_service.create_roll_call(sample_rollcall_data)
        rollcall_service.start_roll_call(created.id)
        rollcall_service.complete_current_stop(created.id)

        stats = rollcall_service.get_progress_stats(created.id)

        assert stats["progress_percentage"] == 50.0  # 1 of 2 stops