"""
Tests for RollCallGeneratorService.

Tests schedule-aware roll call generation with route optimization.
"""
from datetime import datetime, date
import pytest

from app.services.rollcall_generator_service import (
    RollCallGeneratorService,
    GeneratedRollCall,
    ExpectedPrisoner,
    RouteStopInfo,
)
from app.services.pathfinding_service import PathfindingService
from app.db.repositories.location_repo import LocationRepository
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.schedule_repo import ScheduleRepository
from app.db.repositories.connection_repo import ConnectionRepository
from app.models.location import LocationCreate, LocationType
from app.models.inmate import InmateCreate, InmateUpdate
from app.models.schedule import ScheduleEntryCreate, ActivityType


@pytest.fixture
def generator_service(test_db):
    """Create RollCallGeneratorService with test database."""
    from app.db.database import get_connection

    conn = get_connection(test_db)

    location_repo = LocationRepository(conn)
    inmate_repo = InmateRepository(conn)
    schedule_repo = ScheduleRepository(conn)
    connection_repo = ConnectionRepository(conn)
    pathfinding_service = PathfindingService(connection_repo, location_repo)

    service = RollCallGeneratorService(
        location_repo=location_repo,
        inmate_repo=inmate_repo,
        schedule_repo=schedule_repo,
        pathfinding_service=pathfinding_service,
    )

    return service, {
        "location_repo": location_repo,
        "inmate_repo": inmate_repo,
        "schedule_repo": schedule_repo,
        "connection_repo": connection_repo,
    }


@pytest.fixture
def location_hierarchy(generator_service):
    """Create a test location hierarchy: Houseblock -> Wing -> Landing -> Cells."""
    service, repos = generator_service
    location_repo = repos["location_repo"]

    houseblock = location_repo.create(LocationCreate(
        name="Houseblock 1",
        type=LocationType.HOUSEBLOCK,
        building="Block 1",
    ))

    wing_a = location_repo.create(LocationCreate(
        name="A Wing",
        type=LocationType.WING,
        building="Block 1",
        parent_id=houseblock.id,
    ))

    wing_b = location_repo.create(LocationCreate(
        name="B Wing",
        type=LocationType.WING,
        building="Block 1",
        parent_id=houseblock.id,
    ))

    landing_a1 = location_repo.create(LocationCreate(
        name="A1s",
        type=LocationType.LANDING,
        building="Block 1",
        parent_id=wing_a.id,
        floor=0,
    ))

    landing_a2 = location_repo.create(LocationCreate(
        name="A2s",
        type=LocationType.LANDING,
        building="Block 1",
        parent_id=wing_a.id,
        floor=1,
    ))

    landing_b1 = location_repo.create(LocationCreate(
        name="B1s",
        type=LocationType.LANDING,
        building="Block 1",
        parent_id=wing_b.id,
        floor=0,
    ))

    cells_a1 = []
    for i in range(1, 4):
        cell = location_repo.create(LocationCreate(
            name=f"A1-{i:02d}",
            type=LocationType.CELL,
            building="Block 1",
            parent_id=landing_a1.id,
            floor=0,
            capacity=2,
        ))
        cells_a1.append(cell)

    cells_a2 = []
    for i in range(1, 3):
        cell = location_repo.create(LocationCreate(
            name=f"A2-{i:02d}",
            type=LocationType.CELL,
            building="Block 1",
            parent_id=landing_a2.id,
            floor=1,
            capacity=2,
        ))
        cells_a2.append(cell)

    cells_b1 = []
    for i in range(1, 3):
        cell = location_repo.create(LocationCreate(
            name=f"B1-{i:02d}",
            type=LocationType.CELL,
            building="Block 1",
            parent_id=landing_b1.id,
            floor=0,
            capacity=2,
        ))
        cells_b1.append(cell)

    return {
        "houseblock": houseblock,
        "wing_a": wing_a,
        "wing_b": wing_b,
        "landing_a1": landing_a1,
        "landing_a2": landing_a2,
        "landing_b1": landing_b1,
        "cells_a1": cells_a1,
        "cells_a2": cells_a2,
        "cells_b1": cells_b1,
    }


class TestRollCallGeneratorServiceSingleLocation:
    """Test roll call generation with single location."""

    def test_generate_rollcall_single_houseblock(
        self, generator_service, location_hierarchy
    ):
        """Should find all cells under a houseblock."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["houseblock"].id],
            scheduled_at=scheduled_at,
        )

        assert isinstance(result, GeneratedRollCall)
        assert result.location_ids == [locations["houseblock"].id]
        assert result.location_names == ["Houseblock 1"]
        assert result.total_locations == 7  # 3 + 2 + 2 cells

    def test_generate_rollcall_single_wing(
        self, generator_service, location_hierarchy
    ):
        """Should find all cells under a wing."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["wing_a"].id],
            scheduled_at=scheduled_at,
        )

        assert result.location_ids == [locations["wing_a"].id]
        assert result.location_names == ["A Wing"]
        assert result.total_locations == 5  # 3 + 2 cells

    def test_generate_rollcall_single_landing(
        self, generator_service, location_hierarchy
    ):
        """Should find all cells on a landing."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["landing_a1"].id],
            scheduled_at=scheduled_at,
        )

        assert result.location_ids == [locations["landing_a1"].id]
        assert result.location_names == ["A1s"]
        assert result.total_locations == 3

    def test_generate_rollcall_single_cell(
        self, generator_service, location_hierarchy
    ):
        """Should handle a single cell location."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["cells_a1"][0].id],
            scheduled_at=scheduled_at,
        )

        assert result.location_ids == [locations["cells_a1"][0].id]
        assert result.location_names == ["A1-01"]
        assert result.total_locations == 1


class TestRollCallGeneratorServiceMultipleLocations:
    """Test roll call generation with multiple locations."""

    def test_generate_rollcall_two_wings(
        self, generator_service, location_hierarchy
    ):
        """Should combine cells from two wings."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["wing_a"].id, locations["wing_b"].id],
            scheduled_at=scheduled_at,
        )

        assert result.location_ids == [locations["wing_a"].id, locations["wing_b"].id]
        assert result.location_names == ["A Wing", "B Wing"]
        assert result.total_locations == 7  # 5 + 2 cells

    def test_generate_rollcall_two_landings_same_wing(
        self, generator_service, location_hierarchy
    ):
        """Should combine cells from two landings in same wing."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["landing_a1"].id, locations["landing_a2"].id],
            scheduled_at=scheduled_at,
        )

        assert result.location_ids == [locations["landing_a1"].id, locations["landing_a2"].id]
        assert result.location_names == ["A1s", "A2s"]
        assert result.total_locations == 5  # 3 + 2 cells

    def test_generate_rollcall_mixed_hierarchy_levels(
        self, generator_service, location_hierarchy
    ):
        """Should handle mixed hierarchy levels (wing + landing + cell)."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[
                locations["wing_b"].id,  # B Wing (2 cells)
                locations["landing_a1"].id,  # A1s landing (3 cells)
                locations["cells_a2"][0].id,  # One cell from A2s
            ],
            scheduled_at=scheduled_at,
        )

        assert result.location_ids == [locations["wing_b"].id, locations["landing_a1"].id, locations["cells_a2"][0].id]
        assert result.total_locations == 6  # 2 + 3 + 1 cells

    def test_generate_rollcall_specific_cells(
        self, generator_service, location_hierarchy
    ):
        """Should handle arbitrary selection of specific cells."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        # Select 5 random cells across the prison
        selected_cells = [
            locations["cells_a1"][0].id,
            locations["cells_a1"][2].id,
            locations["cells_a2"][0].id,
            locations["cells_b1"][0].id,
            locations["cells_b1"][1].id,
        ]

        result = service.generate_roll_call(
            location_ids=selected_cells,
            scheduled_at=scheduled_at,
        )

        assert result.total_locations == 5

    def test_generate_rollcall_overlapping_hierarchies_deduplicates(
        self, generator_service, location_hierarchy
    ):
        """Should deduplicate cells when hierarchies overlap."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        # Specify both wing AND one of its landings
        result = service.generate_roll_call(
            location_ids=[
                locations["wing_a"].id,  # Includes landing_a1 and landing_a2
                locations["landing_a1"].id,  # Overlaps with wing_a
            ],
            scheduled_at=scheduled_at,
        )

        # Should still only have 5 cells (no duplicates)
        assert result.total_locations == 5


class TestRollCallGeneratorServiceValidation:
    """Test input validation."""

    def test_generate_rollcall_empty_list_raises(
        self, generator_service
    ):
        """Should raise ValueError for empty location list."""
        service, repos = generator_service

        with pytest.raises(ValueError, match="At least one location ID required"):
            service.generate_roll_call(
                location_ids=[],
                scheduled_at=datetime.now(),
            )

    def test_generate_rollcall_invalid_location_raises(
        self, generator_service
    ):
        """Should raise ValueError for non-existent location."""
        service, repos = generator_service

        with pytest.raises(ValueError, match="not found"):
            service.generate_roll_call(
                location_ids=["non-existent-id"],
                scheduled_at=datetime.now(),
            )

    def test_generate_rollcall_no_cells_found_raises(
        self, generator_service, location_hierarchy
    ):
        """Should raise ValueError when no cells found in locations."""
        service, repos = generator_service
        locations = location_hierarchy
        location_repo = repos["location_repo"]

        # Create a location with no cell descendants
        gym = location_repo.create(LocationCreate(
            name="Gym",
            type=LocationType.GYM,
            building="Block 1",
        ))

        with pytest.raises(ValueError, match="No cells found"):
            service.generate_roll_call(
                location_ids=[gym.id],
                scheduled_at=datetime.now(),
            )


class TestRollCallGeneratorServiceRouteAndStats:
    """Test route generation and statistics."""

    def test_generate_rollcall_includes_route_with_stops(
        self, generator_service, location_hierarchy
    ):
        """Should generate route with all cell stops."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["landing_a1"].id],
            scheduled_at=scheduled_at,
            include_empty=True,
        )

        assert len(result.route) == 3  # 3 cells
        assert all(isinstance(stop, RouteStopInfo) for stop in result.route)
        assert all(stop.location_type == "cell" for stop in result.route)

    def test_generate_rollcall_counts_empty_vs_occupied(
        self, generator_service, location_hierarchy
    ):
        """Should correctly count occupied and empty locations."""
        service, repos = generator_service
        locations = location_hierarchy
        inmate_repo = repos["inmate_repo"]

        # Create an inmate in first cell
        inmate = inmate_repo.create(InmateCreate(
            inmate_number="A001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
        ))
        # Set home_cell_id
        inmate_repo.update(inmate.id, InmateUpdate(home_cell_id=locations["cells_a1"][0].id))

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["landing_a1"].id],
            scheduled_at=scheduled_at,
        )

        assert result.occupied_locations == 1
        assert result.empty_locations == 2
        assert result.total_prisoners_expected == 1

    def test_generate_rollcall_excludes_empty_when_requested(
        self, generator_service, location_hierarchy
    ):
        """Should exclude empty cells when include_empty=False."""
        service, repos = generator_service
        locations = location_hierarchy
        inmate_repo = repos["inmate_repo"]

        # Create an inmate in first cell only
        inmate = inmate_repo.create(InmateCreate(
            inmate_number="A001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
        ))
        inmate_repo.update(inmate.id, InmateUpdate(home_cell_id=locations["cells_a1"][0].id))

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["landing_a1"].id],
            scheduled_at=scheduled_at,
            include_empty=False,
        )

        # Route should only include occupied cells
        assert len(result.route) == 1
        assert result.route[0].is_occupied is True

    def test_summary_includes_estimated_time(
        self, generator_service, location_hierarchy
    ):
        """Should include estimated verification time."""
        service, repos = generator_service
        locations = location_hierarchy

        scheduled_at = datetime(2026, 1, 29, 14, 0, 0)

        result = service.generate_roll_call(
            location_ids=[locations["landing_a1"].id],
            scheduled_at=scheduled_at,
        )

        # With 0 prisoners, estimated time is just walking time
        assert result.estimated_time_seconds >= 0


class TestRollCallGeneratorServiceExpectedPrisoners:
    """Test expected prisoner lookup."""

    def test_get_expected_prisoners_returns_home_cell_inmates(
        self, generator_service, location_hierarchy
    ):
        """Should return inmates whose home cell this is."""
        service, repos = generator_service
        locations = location_hierarchy
        inmate_repo = repos["inmate_repo"]

        # Create inmate in first cell
        inmate = inmate_repo.create(InmateCreate(
            inmate_number="A001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
        ))
        inmate_repo.update(inmate.id, InmateUpdate(home_cell_id=locations["cells_a1"][0].id))

        at_time = datetime(2026, 1, 29, 14, 0, 0)

        result = service.get_expected_prisoners(
            location_id=locations["cells_a1"][0].id,
            at_time=at_time,
        )

        assert len(result) == 1
        assert result[0].inmate.id == inmate.id
        assert result[0].is_at_home_cell is True

    def test_get_expected_prisoners_empty_cell_returns_empty_list(
        self, generator_service, location_hierarchy
    ):
        """Should return empty list for cell with no inmates."""
        service, repos = generator_service
        locations = location_hierarchy

        at_time = datetime(2026, 1, 29, 14, 0, 0)

        result = service.get_expected_prisoners(
            location_id=locations["cells_a1"][0].id,
            at_time=at_time,
        )

        assert result == []


class TestRollCallGeneratorServicePriority:
    """Test priority scoring."""

    def test_priority_increases_with_imminent_appointment(
        self, generator_service, location_hierarchy
    ):
        """Should give higher priority to prisoners with imminent appointments."""
        service, repos = generator_service
        locations = location_hierarchy
        inmate_repo = repos["inmate_repo"]
        schedule_repo = repos["schedule_repo"]

        # Create inmate
        inmate = inmate_repo.create(InmateCreate(
            inmate_number="A001",
            first_name="John",
            last_name="Doe",
            date_of_birth=date(1990, 1, 1),
            cell_block="A",
            cell_number="101",
        ))
        inmate_repo.update(inmate.id, InmateUpdate(home_cell_id=locations["cells_a1"][0].id))

        # Create healthcare appointment in 10 minutes
        schedule_repo.create(ScheduleEntryCreate(
            inmate_id=inmate.id,
            location_id=locations["houseblock"].id,  # Different location
            day_of_week=3,  # Thursday (matching our test time)
            start_time="14:10",
            end_time="15:00",
            activity_type=ActivityType.HEALTHCARE,
        ))

        # Thursday at 14:00
        at_time = datetime(2026, 1, 29, 14, 0, 0)  # Thursday

        result = service.get_expected_prisoners(
            location_id=locations["cells_a1"][0].id,
            at_time=at_time,
        )

        # Should have high priority due to imminent healthcare appointment
        assert len(result) == 1
        assert result[0].priority_score > 50  # Base is 50
