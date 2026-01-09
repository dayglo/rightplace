"""
Test suite for RollCallRepository.

Tests CRUD operations, status transitions, and route management for roll calls.
"""
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.db.database import get_connection, init_db
from app.db.repositories.rollcall_repo import RollCallRepository
from app.models.rollcall import (
    RollCall,
    RollCallCreate,
    RollCallStatus,
    RouteStop,
)


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
            expected_inmates=["inmate3", "inmate4"],
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


class TestRollCallRepositoryCreate:
    """Test roll call creation."""

    def test_create_rollcall_success(self, rollcall_repo, sample_rollcall_data):
        """Should create roll call with all required fields."""
        rollcall = rollcall_repo.create(sample_rollcall_data)

        assert rollcall.id is not None
        assert rollcall.name == "Morning Roll Call"
        assert rollcall.status == RollCallStatus.SCHEDULED
        assert rollcall.officer_id == "officer1"
        assert rollcall.notes == "Test roll call"
        assert len(rollcall.route) == 2
        assert rollcall.started_at is None
        assert rollcall.completed_at is None

    def test_create_rollcall_route_serialization(
        self, rollcall_repo, sample_rollcall_data
    ):
        """Should correctly serialize route stops to JSON."""
        rollcall = rollcall_repo.create(sample_rollcall_data)

        assert rollcall.route[0].id == "stop1"
        assert rollcall.route[0].location_id == "loc1"
        assert rollcall.route[0].order == 1
        assert rollcall.route[0].expected_inmates == ["inmate1", "inmate2"]
        assert rollcall.route[0].status == "pending"

    def test_create_multiple_rollcalls(self, rollcall_repo, sample_route_stops):
        """Should create multiple roll calls with unique IDs."""
        rollcall1 = rollcall_repo.create(
            RollCallCreate(
                name="Morning Roll Call",
                scheduled_at=datetime.now(),
                route=sample_route_stops,
                officer_id="officer1",
            )
        )
        rollcall2 = rollcall_repo.create(
            RollCallCreate(
                name="Evening Roll Call",
                scheduled_at=datetime.now() + timedelta(hours=8),
                route=sample_route_stops,
                officer_id="officer2",
            )
        )

        assert rollcall1.id != rollcall2.id
        assert rollcall1.name != rollcall2.name


class TestRollCallRepositoryRead:
    """Test reading roll call records."""

    def test_get_by_id_found(self, rollcall_repo, sample_rollcall_data):
        """Should retrieve roll call by ID."""
        created = rollcall_repo.create(sample_rollcall_data)
        retrieved = rollcall_repo.get_by_id(created.id)

        assert retrieved is not None
        assert retrieved.id == created.id
        assert retrieved.name == created.name
        assert len(retrieved.route) == len(created.route)

    def test_get_by_id_not_found(self, rollcall_repo):
        """Should return None for non-existent ID."""
        result = rollcall_repo.get_by_id("non-existent-id")
        assert result is None

    def test_get_all_empty(self, rollcall_repo):
        """Should return empty list when no roll calls exist."""
        rollcalls = rollcall_repo.get_all()
        assert rollcalls == []

    def test_get_all_multiple(self, rollcall_repo, sample_route_stops):
        """Should return all roll calls."""
        rollcall_repo.create(
            RollCallCreate(
                name="Morning Roll Call",
                scheduled_at=datetime.now(),
                route=sample_route_stops,
                officer_id="officer1",
            )
        )
        rollcall_repo.create(
            RollCallCreate(
                name="Evening Roll Call",
                scheduled_at=datetime.now() + timedelta(hours=8),
                route=sample_route_stops,
                officer_id="officer1",
            )
        )

        rollcalls = rollcall_repo.get_all()
        assert len(rollcalls) == 2

    def test_get_by_status(self, rollcall_repo, sample_rollcall_data):
        """Should retrieve roll calls by status."""
        created = rollcall_repo.create(sample_rollcall_data)

        scheduled_rollcalls = rollcall_repo.get_by_status(RollCallStatus.SCHEDULED)
        assert len(scheduled_rollcalls) == 1
        assert scheduled_rollcalls[0].id == created.id

        in_progress_rollcalls = rollcall_repo.get_by_status(
            RollCallStatus.IN_PROGRESS
        )
        assert len(in_progress_rollcalls) == 0

    def test_get_by_officer(self, rollcall_repo, sample_route_stops):
        """Should retrieve roll calls by officer."""
        rollcall_repo.create(
            RollCallCreate(
                name="Roll Call 1",
                scheduled_at=datetime.now(),
                route=sample_route_stops,
                officer_id="officer1",
            )
        )
        rollcall_repo.create(
            RollCallCreate(
                name="Roll Call 2",
                scheduled_at=datetime.now(),
                route=sample_route_stops,
                officer_id="officer1",
            )
        )
        rollcall_repo.create(
            RollCallCreate(
                name="Roll Call 3",
                scheduled_at=datetime.now(),
                route=sample_route_stops,
                officer_id="officer2",
            )
        )

        officer1_rollcalls = rollcall_repo.get_by_officer("officer1")
        assert len(officer1_rollcalls) == 2


class TestRollCallRepositoryUpdate:
    """Test updating roll call records."""

    def test_update_status_to_in_progress(self, rollcall_repo, sample_rollcall_data):
        """Should update status to in_progress and set started_at."""
        created = rollcall_repo.create(sample_rollcall_data)

        updated = rollcall_repo.update_status(
            created.id, RollCallStatus.IN_PROGRESS
        )

        assert updated is not None
        assert updated.status == RollCallStatus.IN_PROGRESS
        assert updated.started_at is not None
        assert updated.completed_at is None

    def test_update_status_to_completed(self, rollcall_repo, sample_rollcall_data):
        """Should update status to completed and set completed_at."""
        created = rollcall_repo.create(sample_rollcall_data)
        rollcall_repo.update_status(created.id, RollCallStatus.IN_PROGRESS)

        updated = rollcall_repo.update_status(created.id, RollCallStatus.COMPLETED)

        assert updated is not None
        assert updated.status == RollCallStatus.COMPLETED
        assert updated.started_at is not None
        assert updated.completed_at is not None

    def test_update_status_to_cancelled(self, rollcall_repo, sample_rollcall_data):
        """Should update status to cancelled with reason."""
        created = rollcall_repo.create(sample_rollcall_data)

        updated = rollcall_repo.update_status(
            created.id,
            RollCallStatus.CANCELLED,
            cancelled_reason="Emergency situation",
        )

        assert updated is not None
        assert updated.status == RollCallStatus.CANCELLED
        assert updated.cancelled_reason == "Emergency situation"

    def test_update_status_not_found(self, rollcall_repo):
        """Should return None when updating non-existent roll call."""
        result = rollcall_repo.update_status(
            "non-existent-id", RollCallStatus.IN_PROGRESS
        )
        assert result is None

    def test_update_route_stop_status(self, rollcall_repo, sample_rollcall_data):
        """Should update route stop status."""
        created = rollcall_repo.create(sample_rollcall_data)

        updated = rollcall_repo.update_route_stop(
            created.id, "stop1", "completed"
        )

        assert updated is not None
        assert updated.route[0].status == "completed"
        assert updated.route[0].completed_at is not None
        assert updated.route[1].status == "pending"

    def test_update_route_stop_with_skip_reason(
        self, rollcall_repo, sample_rollcall_data
    ):
        """Should update route stop status with skip reason."""
        created = rollcall_repo.create(sample_rollcall_data)

        updated = rollcall_repo.update_route_stop(
            created.id, "stop1", "skipped", skip_reason="Location inaccessible"
        )

        assert updated is not None
        assert updated.route[0].status == "skipped"
        assert updated.route[0].skip_reason == "Location inaccessible"


class TestRollCallRepositoryDelete:
    """Test deleting roll call records."""

    def test_delete_success(self, rollcall_repo, sample_rollcall_data):
        """Should delete roll call."""
        created = rollcall_repo.create(sample_rollcall_data)
        result = rollcall_repo.delete(created.id)

        assert result is True
        assert rollcall_repo.get_by_id(created.id) is None

    def test_delete_not_found(self, rollcall_repo):
        """Should return False when deleting non-existent roll call."""
        result = rollcall_repo.delete("non-existent-id")
        assert result is False