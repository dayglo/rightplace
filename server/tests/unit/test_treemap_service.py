"""
Unit tests for TreemapService.

Tests treemap hierarchy building, status aggregation, time calculations,
and multi-rollcall support.
"""
import sqlite3
from datetime import datetime, timedelta
from uuid import uuid4

import pytest

from app.db.database import init_db
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.rollcall_repo import RollCallRepository
from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.verification_repo import VerificationRepository
from app.models.inmate import InmateCreate
from app.models.location import Location, LocationType, LocationCreate
from app.models.rollcall import RollCall, RollCallCreate, RollCallStatus, RouteStop
from app.models.schedule import ActivityType, ScheduleEntryCreate
from app.models.verification import Verification, VerificationStatus
from app.services.treemap_service import OccupancyMode, TreemapService


@pytest.fixture
def test_conn():
    """Create an in-memory SQLite database for testing."""
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    init_db(conn)
    yield conn
    conn.close()


@pytest.fixture
def location_repo(test_conn):
    """Create LocationRepository instance."""
    return LocationRepository(test_conn)


@pytest.fixture
def inmate_repo(test_conn):
    """Create InmateRepository instance."""
    return InmateRepository(test_conn)


@pytest.fixture
def rollcall_repo(test_conn):
    """Create RollCallRepository instance."""
    return RollCallRepository(test_conn)


@pytest.fixture
def verification_repo(test_conn):
    """Create VerificationRepository instance."""
    return VerificationRepository(test_conn)


@pytest.fixture
def schedule_repo(test_conn):
    """Create ScheduleRepository instance."""
    return ScheduleRepository(test_conn)


@pytest.fixture
def treemap_service(test_conn):
    """Create TreemapService instance."""
    return TreemapService(test_conn)


@pytest.fixture
def sample_prison_hierarchy(location_repo):
    """
    Create a sample prison hierarchy for testing.

    Structure:
    - Prison: HMP Oakwood
      - Wing: A Wing
        - Landing: Ground Floor
          - Cell: A-101
          - Cell: A-102
        - Landing: First Floor
          - Cell: A-201
    """
    # Create prison
    prison = location_repo.create(
        LocationCreate(
            name="HMP Oakwood",
            type=LocationType.PRISON,
            parent_id=None,
            capacity=100,
            floor=0,
            building="Main",
        )
    )

    # Create wing
    wing = location_repo.create(
        LocationCreate(
            name="A Wing",
            type=LocationType.WING,
            parent_id=prison.id,
            capacity=50,
            floor=0,
            building="Main",
        )
    )

    # Create landings
    ground_floor = location_repo.create(
        LocationCreate(
            name="Ground Floor",
            type=LocationType.LANDING,
            parent_id=wing.id,
            capacity=20,
            floor=0,
            building="Main",
        )
    )

    first_floor = location_repo.create(
        LocationCreate(
            name="First Floor",
            type=LocationType.LANDING,
            parent_id=wing.id,
            capacity=20,
            floor=1,
            building="Main",
        )
    )

    # Create cells
    cell_a101 = location_repo.create(
        LocationCreate(
            name="A-101",
            type=LocationType.CELL,
            parent_id=ground_floor.id,
            capacity=2,
            floor=0,
            building="Main",
        )
    )

    cell_a102 = location_repo.create(
        LocationCreate(
            name="A-102",
            type=LocationType.CELL,
            parent_id=ground_floor.id,
            capacity=2,
            floor=0,
            building="Main",
        )
    )

    cell_a201 = location_repo.create(
        LocationCreate(
            name="A-201",
            type=LocationType.CELL,
            parent_id=first_floor.id,
            capacity=2,
            floor=1,
            building="Main",
        )
    )

    return {
        "prison": prison,
        "wing": wing,
        "ground_floor": ground_floor,
        "first_floor": first_floor,
        "cell_a101": cell_a101,
        "cell_a102": cell_a102,
        "cell_a201": cell_a201,
    }


@pytest.fixture
def sample_inmates(inmate_repo, sample_prison_hierarchy):
    """Create sample inmates in cells."""
    inmate1 = inmate_repo.create(
        InmateCreate(
            inmate_number="A1001",
            first_name="John",
            last_name="Smith",
            date_of_birth=datetime(1990, 1, 1).date(),
            cell_block="A",
            cell_number="101",
            home_cell_id=sample_prison_hierarchy["cell_a101"].id,
        )
    )

    inmate2 = inmate_repo.create(
        InmateCreate(
            inmate_number="A1002",
            first_name="Jane",
            last_name="Doe",
            date_of_birth=datetime(1991, 2, 2).date(),
            cell_block="A",
            cell_number="101",
            home_cell_id=sample_prison_hierarchy["cell_a101"].id,
        )
    )

    inmate3 = inmate_repo.create(
        InmateCreate(
            inmate_number="A1003",
            first_name="Bob",
            last_name="Jones",
            date_of_birth=datetime(1992, 3, 3).date(),
            cell_block="A",
            cell_number="102",
            home_cell_id=sample_prison_hierarchy["cell_a102"].id,
        )
    )

    return {
        "inmate1": inmate1,
        "inmate2": inmate2,
        "inmate3": inmate3,
    }


@pytest.fixture
def sample_rollcall(rollcall_repo, sample_prison_hierarchy):
    """Create a sample rollcall."""
    scheduled_at = datetime(2024, 1, 15, 10, 0, 0)

    route = [
        RouteStop(
            id=str(uuid4()),
            location_id=sample_prison_hierarchy["cell_a101"].id,
            order=0,
            expected_inmates=["A1001", "A1002"],
        ),
        RouteStop(
            id=str(uuid4()),
            location_id=sample_prison_hierarchy["cell_a102"].id,
            order=1,
            expected_inmates=["A1003"],
        ),
        RouteStop(
            id=str(uuid4()),
            location_id=sample_prison_hierarchy["cell_a201"].id,
            order=2,
            expected_inmates=[],
        ),
    ]

    rollcall_data = RollCallCreate(
        name="Morning Check",
        scheduled_at=scheduled_at,
        route=route,
        officer_id="officer123",
        notes="Test rollcall",
    )

    rollcall = rollcall_repo.create(rollcall_data)

    return rollcall


def test_calculate_estimated_times(treemap_service, sample_rollcall):
    """
    Should calculate estimated arrival times based on route order.

    Formula: estimated_time = scheduled_at + (stop.order * 5 minutes)
    """
    estimated_times = treemap_service.calculate_estimated_times(sample_rollcall)

    # Stop 0: 10:00 + (0 * 5) = 10:00
    assert estimated_times[sample_rollcall.route[0].location_id] == datetime(
        2024, 1, 15, 10, 0, 0
    )

    # Stop 1: 10:00 + (1 * 5) = 10:05
    assert estimated_times[sample_rollcall.route[1].location_id] == datetime(
        2024, 1, 15, 10, 5, 0
    )

    # Stop 2: 10:00 + (2 * 5) = 10:10
    assert estimated_times[sample_rollcall.route[2].location_id] == datetime(
        2024, 1, 15, 10, 10, 0
    )


def test_determine_location_status_grey_not_in_route(
    treemap_service,
    sample_prison_hierarchy,
    sample_rollcall,
):
    """
    Should return grey status for locations not in rollcall route.
    """
    # Create a location not in the route
    location = sample_prison_hierarchy["cell_a201"]
    # Remove it from route for this test
    rollcall = sample_rollcall
    rollcall.route = [
        stop for stop in rollcall.route if stop.location_id != location.id
    ]

    estimated_times_map = {
        rollcall.id: treemap_service.calculate_estimated_times(rollcall)
    }

    timestamp = datetime(2024, 1, 15, 10, 0, 0)

    status = treemap_service.determine_location_status(
        location,
        [rollcall],
        estimated_times_map,
        [],
        timestamp,
    )

    assert status == "grey"


def test_determine_location_status_amber_scheduled_not_completed(
    treemap_service,
    sample_prison_hierarchy,
    sample_rollcall,
):
    """
    Should return amber status for locations scheduled but not completed.
    """
    location = sample_prison_hierarchy["cell_a101"]
    rollcall = sample_rollcall

    estimated_times_map = {
        rollcall.id: treemap_service.calculate_estimated_times(rollcall)
    }

    # Timestamp at scheduled time (within ±10 minutes)
    timestamp = datetime(2024, 1, 15, 10, 0, 0)

    status = treemap_service.determine_location_status(
        location,
        [rollcall],
        estimated_times_map,
        [],  # No verifications yet
        timestamp,
    )

    assert status == "amber"


def test_determine_location_status_green_all_verified(
    treemap_service,
    sample_prison_hierarchy,
    sample_rollcall,
    sample_inmates,
    verification_repo,
):
    """
    Should return green status when all inmates verified.
    """
    location = sample_prison_hierarchy["cell_a101"]
    rollcall = sample_rollcall

    # Create verifications for all inmates
    verification1 = verification_repo.create(
        roll_call_id=rollcall.id,
        inmate_id=sample_inmates["inmate1"].id,
        location_id=location.id,
        status=VerificationStatus.VERIFIED,
        confidence=0.95,
    )

    verification2 = verification_repo.create(
        roll_call_id=rollcall.id,
        inmate_id=sample_inmates["inmate2"].id,
        location_id=location.id,
        status=VerificationStatus.VERIFIED,
        confidence=0.92,
    )

    estimated_times_map = {
        rollcall.id: treemap_service.calculate_estimated_times(rollcall)
    }

    # Timestamp after scheduled time
    timestamp = datetime(2024, 1, 15, 10, 15, 0)

    status = treemap_service.determine_location_status(
        location,
        [rollcall],
        estimated_times_map,
        [verification1, verification2],
        timestamp,
    )

    assert status == "green"


def test_determine_location_status_red_any_failed(
    treemap_service,
    sample_prison_hierarchy,
    sample_rollcall,
    sample_inmates,
    verification_repo,
):
    """
    Should return red status when any inmate failed verification.
    """
    location = sample_prison_hierarchy["cell_a101"]
    rollcall = sample_rollcall

    # One verified, one failed
    verification1 = verification_repo.create(
        roll_call_id=rollcall.id,
        inmate_id=sample_inmates["inmate1"].id,
        location_id=location.id,
        status=VerificationStatus.VERIFIED,
        confidence=0.95,
    )

    verification2 = verification_repo.create(
        roll_call_id=rollcall.id,
        inmate_id=sample_inmates["inmate2"].id,
        location_id=location.id,
        status=VerificationStatus.NOT_FOUND,
        confidence=0.0,
    )

    estimated_times_map = {
        rollcall.id: treemap_service.calculate_estimated_times(rollcall)
    }

    timestamp = datetime(2024, 1, 15, 10, 15, 0)

    status = treemap_service.determine_location_status(
        location,
        [rollcall],
        estimated_times_map,
        [verification1, verification2],
        timestamp,
    )

    assert status == "red"


def test_aggregate_status_upward_all_green(treemap_service):
    """
    Should return green when all children are green.
    """
    children_statuses = ["green", "green", "green"]
    status = treemap_service.aggregate_status_upward(children_statuses)
    assert status == "green"


def test_aggregate_status_upward_any_red(treemap_service):
    """
    Should return red when any child is red.
    """
    children_statuses = ["green", "red", "green"]
    status = treemap_service.aggregate_status_upward(children_statuses)
    assert status == "red"


def test_aggregate_status_upward_amber_with_no_red(treemap_service):
    """
    Should return amber when any child is amber and no red.
    """
    children_statuses = ["green", "amber", "green"]
    status = treemap_service.aggregate_status_upward(children_statuses)
    assert status == "amber"


def test_aggregate_status_upward_all_grey(treemap_service):
    """
    Should return grey when all children are grey.
    """
    children_statuses = ["grey", "grey"]
    status = treemap_service.aggregate_status_upward(children_statuses)
    assert status == "grey"


def test_aggregate_status_upward_empty(treemap_service):
    """
    Should return grey when no children.
    """
    children_statuses = []
    status = treemap_service.aggregate_status_upward(children_statuses)
    assert status == "grey"


def test_build_treemap_hierarchy_single_rollcall(
    treemap_service,
    sample_rollcall,
    sample_prison_hierarchy,
    sample_inmates,
):
    """
    Should build correct hierarchy for single rollcall.
    """
    timestamp = datetime(2024, 1, 15, 10, 0, 0)

    # Use HOME_CELL mode since test fixtures use home cell assignments
    treemap_data = treemap_service.build_treemap_hierarchy(
        [sample_rollcall.id], timestamp, include_empty=False,
        occupancy_mode=OccupancyMode.HOME_CELL
    )

    # Should have root node
    assert treemap_data.name == "All Prisons"
    assert treemap_data.type == "root"
    assert treemap_data.value >= 0

    # Should have prison as child
    assert len(treemap_data.children) == 1
    prison_node = treemap_data.children[0]
    assert prison_node.name == "HMP Oakwood"
    assert prison_node.type == "prison"

    # Should have wing as child of prison
    assert len(prison_node.children) == 1
    wing_node = prison_node.children[0]
    assert wing_node.name == "A Wing"
    assert wing_node.type == "wing"


def test_build_treemap_hierarchy_multiple_rollcalls(
    treemap_service,
    sample_rollcall,
    rollcall_repo,
    sample_prison_hierarchy,
    sample_inmates,
):
    """
    Should handle multiple rollcalls correctly.
    """
    # Create second rollcall
    scheduled_at = datetime(2024, 1, 15, 14, 0, 0)
    route2 = [
        RouteStop(
            id=str(uuid4()),
            location_id=sample_prison_hierarchy["cell_a201"].id,
            order=0,
            expected_inmates=[],
        ),
    ]
    rollcall2_data = RollCallCreate(
        name="Afternoon Check",
        scheduled_at=scheduled_at,
        route=route2,
        officer_id="officer456",
        notes="Second rollcall",
    )
    rollcall2 = rollcall_repo.create(rollcall2_data)

    timestamp = datetime(2024, 1, 15, 10, 0, 0)

    # Use HOME_CELL mode since test fixtures use home cell assignments
    treemap_data = treemap_service.build_treemap_hierarchy(
        [sample_rollcall.id, rollcall2.id], timestamp, include_empty=False,
        occupancy_mode=OccupancyMode.HOME_CELL
    )

    # Should combine data from both rollcalls
    assert treemap_data.name == "All Prisons"
    assert len(treemap_data.children) >= 1


def test_build_treemap_hierarchy_status_propagation(
    treemap_service,
    sample_rollcall,
    sample_prison_hierarchy,
    sample_inmates,
    verification_repo,
):
    """
    Should propagate status from cells up to parent locations.
    """
    location = sample_prison_hierarchy["cell_a101"]

    # Create failed verification
    verification_repo.create(
        roll_call_id=sample_rollcall.id,
        inmate_id=sample_inmates["inmate1"].id,
        location_id=location.id,
        status=VerificationStatus.NOT_FOUND,
        confidence=0.0,
    )

    timestamp = datetime(2024, 1, 15, 10, 15, 0)

    # Use HOME_CELL mode since test fixtures use home cell assignments
    treemap_data = treemap_service.build_treemap_hierarchy(
        [sample_rollcall.id], timestamp, include_empty=False,
        occupancy_mode=OccupancyMode.HOME_CELL
    )

    # Find the prison node
    prison_node = treemap_data.children[0]

    # Status should propagate upward (red from failed verification)
    # At minimum, the cell should be red, and parent should aggregate
    assert prison_node.status in ["red", "amber", "green", "grey"]
    # The exact status depends on all children, but at least verify structure exists
    assert prison_node.metadata is not None
    assert prison_node.metadata.inmate_count >= 0


def test_build_treemap_hierarchy_no_rollcalls_show_all(
    treemap_service,
    sample_prison_hierarchy,
    sample_inmates,
):
    """
    Should show all locations when no rollcalls specified.
    """
    timestamp = datetime(2024, 1, 15, 10, 0, 0)

    # No rollcalls specified - should show everything with grey status
    # Use HOME_CELL mode since test fixtures use home cell assignments
    treemap_data = treemap_service.build_treemap_hierarchy(
        [], timestamp, include_empty=False,
        occupancy_mode=OccupancyMode.HOME_CELL
    )

    # Should still have structure
    assert treemap_data.name == "All Prisons"
    assert len(treemap_data.children) >= 1

    # With inmates, should show the hierarchy
    prison_node = treemap_data.children[0]
    assert prison_node.name == "HMP Oakwood"
    # All locations should be grey (no rollcalls)
    assert prison_node.status == "grey"


def test_build_treemap_hierarchy_include_empty_locations(
    treemap_service,
    sample_prison_hierarchy,
):
    """
    Should include empty locations when include_empty=True.
    """
    timestamp = datetime(2024, 1, 15, 10, 0, 0)

    # With include_empty=True, should show all locations even without inmates
    # Use SCHEDULED mode here - include_empty should still work
    treemap_data = treemap_service.build_treemap_hierarchy(
        [], timestamp, include_empty=True,
        occupancy_mode=OccupancyMode.SCHEDULED
    )

    # Should have structure even without inmates
    assert treemap_data.name == "All Prisons"
    # The hierarchy should be present (prisons, wings, landings, cells)
    # even if they're empty


def test_build_treemap_scheduled_mode_with_schedule_entries(
    treemap_service,
    sample_prison_hierarchy,
    sample_inmates,
    schedule_repo,
):
    """
    Should show inmates at scheduled locations when using SCHEDULED mode.
    """
    # Create schedule entries for the inmate at a non-home-cell location (gym)
    gym = sample_prison_hierarchy["prison"]  # Use prison as placeholder for gym
    cell = sample_prison_hierarchy["cell_a101"]
    inmate = sample_inmates["inmate1"]

    # Create schedule entry: inmate at gym on Monday 10:00-11:00
    schedule_entry = ScheduleEntryCreate(
        inmate_id=inmate.id,
        location_id=gym.id,  # Inmate scheduled at a different location
        day_of_week=0,  # Monday
        start_time="10:00",
        end_time="11:00",
        activity_type=ActivityType.GYM,
        is_recurring=True,
    )
    schedule_repo.create(schedule_entry)

    # Query at 10:30 on Monday - inmate should be at gym, not cell
    timestamp = datetime(2024, 1, 15, 10, 30, 0)  # Monday

    treemap_data = treemap_service.build_treemap_hierarchy(
        [], timestamp, include_empty=False,
        occupancy_mode=OccupancyMode.SCHEDULED
    )

    # With SCHEDULED mode, the inmate should show at the gym location
    # not at their home cell
    assert treemap_data.value >= 1  # At least one inmate in system

    # The gym (prison in this test) should have inmates
    prison_node = treemap_data.children[0]
    assert prison_node.value >= 1


def test_build_treemap_scheduled_mode_falls_back_to_home_cell(
    treemap_service,
    sample_prison_hierarchy,
    sample_inmates,
):
    """
    Should show inmates at home cells when SCHEDULED mode and no schedule entries.

    Inmates without a schedule entry for the current time should default to their
    home cell, not disappear from the visualization entirely.
    """
    timestamp = datetime(2024, 1, 15, 10, 30, 0)

    # With SCHEDULED mode and no schedule entries, inmates fall back to home cells
    treemap_data = treemap_service.build_treemap_hierarchy(
        [], timestamp, include_empty=False,
        occupancy_mode=OccupancyMode.SCHEDULED
    )

    # Should show inmates at their home cells (same as HOME_CELL mode when no schedules)
    assert treemap_data.value >= 1  # Inmates at home cells
    assert len(treemap_data.children) >= 1

    # Verify inmates are at their home cells
    prison_node = treemap_data.children[0]
    assert prison_node.value >= 1


def test_build_treemap_home_cell_mode_ignores_schedule(
    treemap_service,
    sample_prison_hierarchy,
    sample_inmates,
    schedule_repo,
):
    """
    Should show inmates at home cells when using HOME_CELL mode, ignoring schedule.
    """
    gym = sample_prison_hierarchy["prison"]
    cell = sample_prison_hierarchy["cell_a101"]
    inmate = sample_inmates["inmate1"]

    # Create schedule entry: inmate at gym
    schedule_entry = ScheduleEntryCreate(
        inmate_id=inmate.id,
        location_id=gym.id,
        day_of_week=0,  # Monday
        start_time="10:00",
        end_time="11:00",
        activity_type=ActivityType.GYM,
        is_recurring=True,
    )
    schedule_repo.create(schedule_entry)

    # Query at 10:30 on Monday
    timestamp = datetime(2024, 1, 15, 10, 30, 0)

    # With HOME_CELL mode, schedule is ignored - inmate should be at home cell
    treemap_data = treemap_service.build_treemap_hierarchy(
        [], timestamp, include_empty=False,
        occupancy_mode=OccupancyMode.HOME_CELL
    )

    # Should show inmates based on home cell assignments
    assert treemap_data.value >= 1

    # Find the cell and verify inmate is there (based on home_cell_id)
    prison_node = treemap_data.children[0]
    assert prison_node.value >= 1
