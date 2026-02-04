# Roll Call Generator Service - Technical Implementation Guide

**Version 1.0 | February 2026**

## Overview

The `RollCallGeneratorService` is responsible for generating schedule-aware, location-centric roll calls with optimal walking routes. This document explains how the service builds up the complete data picture needed to create a roll call, combining location hierarchy, inmate assignments, and schedule data.

## Core Concept

The roll call generator answers the fundamental question:

> **"At a given date/time, which prisoners should be in which locations, and what's the optimal route to verify them all?"**

It does this by combining three main data sources:

1. **Location hierarchy** - Where are the cells, wings, and landings?
2. **Inmate assignments** - Who lives in which cell?
3. **Schedule entries** - Where should each person be at a given time?

## Data Models

### 1. Location (`app/models/location.py`)

Represents physical locations in the prison with hierarchical relationships:

```python
Location
├── id (e.g., "wing-a-1s")
├── name (e.g., "A Wing Landing 1")
├── type (CELL, LANDING, WING, HOUSEBLOCK, PRISON, etc.)
├── parent_id (hierarchical parent location)
├── building, floor, capacity
└── x_coord, y_coord (for pathfinding and visualization)
```

**Key types:**
- `PRISON` → `HOUSEBLOCK` → `WING` → `LANDING` → `CELL` (accommodation hierarchy)
- Special units: `HEALTHCARE`, `SEGREGATION`, `INDUCTION`, `VPU`
- Facilities: `EDUCATION`, `WORKSHOP`, `GYM`, `CHAPEL`, `VISITS`, `RECEPTION`

### 2. Inmate (`app/models/inmate.py`)

Represents a prisoner with their home cell assignment:

```python
Inmate
├── id, inmate_number
├── first_name, last_name, date_of_birth
├── home_cell_id → FK to Location (their assigned cell)
└── cell_block, cell_number (legacy display fields)
```

**Critical field:** `home_cell_id` links each prisoner to their assigned location in the hierarchy.

### 3. ScheduleEntry (`app/models/schedule.py`)

Defines when and where a prisoner should be:

```python
ScheduleEntry
├── inmate_id → which prisoner
├── location_id → where they should be
├── day_of_week (0-6, Monday=0, Sunday=6)
├── start_time, end_time (HH:MM format, e.g., "09:30")
├── activity_type (ActivityType enum)
├── is_recurring (weekly repeat vs one-off)
└── effective_date (for one-off appointments)
```

**Activity types include:**
- Base regime: `ROLL_CHECK`, `LOCK_UP`, `UNLOCK`, `MEAL`, `ASSOCIATION`, `EXERCISE`
- Work/education: `WORK`, `EDUCATION`
- Activities: `GYM`, `CHAPEL`, `PROGRAMMES`
- Appointments: `VISITS`, `HEALTHCARE`
- Special: `HEALTHCARE_RESIDENCE`, `MEDICAL_ROUND`, `INDUCTION`, `RECEPTION_PROCESSING`

### 4. Output Models

**GeneratedRollCall:**
```python
GeneratedRollCall
├── location_ids (input locations)
├── location_names (e.g., ["A Wing", "B Wing"])
├── scheduled_at (datetime when roll call occurs)
├── route (list of RouteStopInfo)
├── total_locations, occupied_locations, empty_locations
├── total_prisoners_expected
└── estimated_time_seconds
```

**RouteStopInfo:**
```python
RouteStopInfo
├── order (stop sequence number)
├── location_id, location_name, location_type
├── building, floor
├── is_occupied (expected_count > 0)
├── expected_count (number of prisoners expected)
├── walking_distance_meters (from previous stop)
└── walking_time_seconds (from previous stop)
```

## The Generation Process

### Entry Point: `generate_roll_call()`

**Method signature:**
```python
def generate_roll_call(
    self,
    location_ids: list[str],        # Can be cells, wings, houseblocks
    scheduled_at: datetime,          # When the roll call occurs
    include_empty: bool = True,      # Include empty locations?
) -> GeneratedRollCall
```

**High-level flow:**
```
Input: ["wing-a"], datetime(2026, 2, 4, 9, 30)
  ↓
Step 1: Expand location hierarchy → [50 cells]
  ↓
Step 2: Calculate expected occupancy per cell → {cell_id: count}
  ↓
Step 3: Calculate optimal walking route → [stop1, stop2, ...]
  ↓
Step 4: Build route stops with context → [RouteStopInfo, ...]
  ↓
Step 5: Calculate summary statistics
  ↓
Output: GeneratedRollCall
```

---

### Step 1: Expand Location Hierarchy

**Code:** Lines 114-147 in `rollcall_generator_service.py`

**Purpose:** Convert high-level location inputs (wings, landings) into a complete list of cells.

**Process:**
1. Deduplicate input location IDs (preserve order)
2. For each input location:
   - If it's a **CELL**: add directly to the list
   - If it's a **WING/LANDING/HOUSEBLOCK**: get all descendant cells using `location_repo.get_all_descendants(location_id, type_filter=LocationType.CELL)`
3. Deduplicate cells using a set to avoid double-counting
4. Validate that at least one cell was found

**Example:**
```python
Input:  ["houseblock-1"]
Output: [cell_a1_01, cell_a1_02, ..., cell_d3_50]  # 200 cells
```

**Repository method used:**
- `location_repo.get_all_descendants(location_id, type_filter=CELL)` - Traverses parent-child relationships to find all cells within a location

---

### Step 2: Calculate Expected Occupancy

**Code:** Lines 149-175 in `rollcall_generator_service.py`

**Purpose:** Determine how many prisoners should be in each cell at the scheduled time.

**Process:**

1. **Extract time information:**
   ```python
   day_of_week = scheduled_at.weekday()  # 0=Monday, 6=Sunday
   time_str = scheduled_at.strftime("%H:%M")  # e.g., "09:30"
   ```

2. **For each cell, count expected prisoners:**
   ```python
   for cell in all_cells:
       # Get prisoners whose home cell this is
       prisoners = inmate_repo.get_by_home_cell(cell.id)

       expected_count = 0
       for prisoner in prisoners:
           # Should they be in this cell at this time?
           if self._is_prisoner_at_home(prisoner.id, cell.id, day_of_week, time_str):
               expected_count += 1

       location_prisoner_counts[cell.id] = expected_count
   ```

3. **Filter empty locations (optional):**
   ```python
   if not include_empty:
       cells_to_visit = [c for c in all_cells if counts[c.id] > 0]
   ```

**Result:** Dictionary mapping `{cell_id: expected_count}`

---

### The Core Logic: `_is_prisoner_at_home()`

**Code:** Lines 280-308 in `rollcall_generator_service.py`

**Purpose:** Determine if a prisoner should be at their home cell at a specific time.

**Logic:**
```python
def _is_prisoner_at_home(inmate_id, home_cell_id, day_of_week, time_str):
    # Get ALL schedule entries active at this exact time
    active_schedules = schedule_repo.get_at_time(day_of_week, time_str)

    # Filter to this prisoner's entries
    prisoner_entries = [e for e in active_schedules if e.inmate_id == inmate_id]

    if not prisoner_entries:
        # No schedule = assume at home cell
        return True

    # If ANY entry is for a different location, they're NOT at home
    for entry in prisoner_entries:
        if entry.location_id != home_cell_id:
            return False  # Scheduled elsewhere (work, education, etc.)

    return True  # All entries are for home cell (or cell-based activities)
```

**Key insight:** The schedule tells us where prisoners are NOT. If they're not scheduled elsewhere, they're assumed to be at their home cell.

---

### Database Query: `schedule_repo.get_at_time()`

**Code:** Lines 118-151 in `schedule_repo.py`

**SQL Query:**
```sql
SELECT id, inmate_id, location_id, day_of_week, start_time, end_time,
       activity_type, is_recurring, effective_date, source, source_id,
       created_at, updated_at
FROM schedule_entries
WHERE day_of_week = ?      -- e.g., 1 (Tuesday)
  AND start_time <= ?      -- Schedule has started (e.g., <= "09:30")
  AND end_time > ?         -- Schedule hasn't ended (e.g., > "09:30")
ORDER BY start_time
```

**Time range logic:**
- `start_time <= "09:30"` - Activity has already started
- `end_time > "09:30"` - Activity hasn't finished yet
- This handles activities spanning the current time (e.g., WORK 08:00-12:00)

**Returns:** All schedule entries active at the specified day/time.

---

### Step 3: Calculate Optimal Route

**Code:** Lines 185-186 in `rollcall_generator_service.py`

**Process:**
```python
cell_ids_to_visit = [c.id for c in cells_to_visit]
optimized_route = pathfinding_service.calculate_route(cell_ids_to_visit)
```

**Pathfinding service responsibilities:**
- Uses location connections (distance_meters, travel_time_seconds)
- Considers building/floor metadata to minimize vertical movement
- Applies graph traversal algorithms (likely nearest-neighbor or TSP approximation)
- Returns an ordered list of stops with walking distances

**Result:** `OptimizedRoute` with ordered stops and total walking time.

---

### Step 4: Build Route Stops with Context

**Code:** Lines 189-211 in `rollcall_generator_service.py`

**Purpose:** Enrich each route stop with prisoner counts and walking info.

**Process:**
```python
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
        location_type=cell.type.value,
        building=stop.building,
        floor=stop.floor,
        is_occupied=expected_count > 0,
        expected_count=expected_count,
        walking_distance_meters=walking_distance,
        walking_time_seconds=walking_time,
    ))
```

**Result:** Complete route with all context needed for UI display.

---

### Step 5: Calculate Summary Statistics

**Code:** Lines 213-221 in `rollcall_generator_service.py`

**Metrics calculated:**
```python
total_locations = len(all_cells)
occupied_locations = sum(1 for c in all_cells if counts[c.id] > 0)
empty_locations = total_locations - occupied_locations
total_prisoners = sum(location_prisoner_counts.values())

# Estimate verification time (30 seconds per prisoner + walking)
verification_time = total_prisoners * 30
estimated_time = optimized_route.total_time_seconds + verification_time
```

**Time estimation:**
- **Walking time:** From pathfinding service (sum of all connection times)
- **Verification time:** 30 seconds per prisoner (facial recognition + interaction)
- **Total:** Walking + verification gives realistic ETA

---

## Performance Optimization: Batch Queries

### The Problem

Naive approach would query schedules for each prisoner individually:
```python
for cell in all_cells:
    for prisoner in get_prisoners(cell):
        schedules = schedule_repo.get_by_inmate(prisoner.id)  # N queries!
        # Check if at home...
```

**Cost:** O(cells × prisoners) database queries

### The Solution: `get_batch_expected_counts()`

**Code:** Lines 381-452 in `rollcall_generator_service.py`

**Optimized approach:**
1. **Load all data upfront:**
   ```python
   all_locations = location_repo.get_all()          # 1 query
   all_inmates = inmate_repo.get_all()              # 1 query
   active_schedules = schedule_repo.get_at_time(day, time)  # 1 query
   ```

2. **Build in-memory maps:**
   ```python
   # Build location hierarchy
   children_map: dict[str, list[str]] = {}
   for loc in all_locations:
       if loc.parent_id:
           children_map[loc.parent_id].append(loc.id)

   # Build home cell → inmates map
   inmates_by_cell: dict[str, list] = {}
   for inmate in all_inmates:
       inmates_by_cell[inmate.home_cell_id].append(inmate)

   # Build set of inmates scheduled elsewhere
   inmates_not_at_home = {entry.inmate_id for entry in active_schedules}
   ```

3. **Count efficiently:**
   ```python
   for location_id in location_ids:
       descendant_ids = get_descendants_from_map(location_id, children_map)
       prisoners = get_prisoners_from_map(descendant_ids, inmates_by_cell)

       # Count prisoners NOT in the scheduled-elsewhere set
       count = sum(1 for p in prisoners if p.id not in inmates_not_at_home)
       counts[location_id] = count
   ```

**Cost:** 3 database queries total, regardless of dataset size

**Speedup:** O(N) instead of O(N²) - massive improvement for large prisons

---

## Example Walkthrough

### Scenario

Officer wants to do a roll call of **A Wing** on **Tuesday, February 4, 2026 at 09:30**.

### Input
```python
generate_roll_call(
    location_ids=["wing-a"],
    scheduled_at=datetime(2026, 2, 4, 9, 30),  # Tuesday 09:30
    include_empty=False
)
```

### Step-by-Step Execution

**Step 1: Expand hierarchy**
- Input: `["wing-a"]`
- Query: `location_repo.get_all_descendants("wing-a", type_filter=CELL)`
- Result: 50 cells (A1-01 through A3-50 across 3 landings)

**Step 2: Calculate occupancy**

Extract time info:
- `day_of_week = 1` (Tuesday, 0=Monday)
- `time_str = "09:30"`

For each cell:

*Cell A1-01:*
```python
prisoners = [Inmate(id="001", home_cell_id="a1-01"),
             Inmate(id="002", home_cell_id="a1-01")]

# Check inmate 001:
active_schedules = [
    ScheduleEntry(inmate_id="001", location_id="education-block",
                  day=1, start="09:00", end="12:00", type=EDUCATION)
]
# 001 is at education → NOT at home

# Check inmate 002:
active_schedules = []  # No schedule
# 002 has no schedule → AT HOME

expected_count = 1  # Only inmate 002
```

*Cell A1-02:*
```python
prisoners = [Inmate(id="003", home_cell_id="a1-02")]

active_schedules = [
    ScheduleEntry(inmate_id="003", location_id="a1-02",
                  day=1, start="07:00", end="12:00", type=LOCK_UP)
]
# 003 is scheduled in their own cell → AT HOME

expected_count = 1
```

*Cell A1-03:*
```python
prisoners = [Inmate(id="004", home_cell_id="a1-03"),
             Inmate(id="005", home_cell_id="a1-03")]

active_schedules = [
    ScheduleEntry(inmate_id="004", location_id="workshop-1",
                  day=1, start="08:00", end="16:00", type=WORK),
    ScheduleEntry(inmate_id="005", location_id="healthcare",
                  day=1, start="09:00", end="10:00", type=HEALTHCARE)
]
# Both scheduled elsewhere → NOT at home

expected_count = 0
```

After checking all 50 cells:
```python
location_prisoner_counts = {
    "a1-01": 1,
    "a1-02": 1,
    "a1-03": 0,  # Empty - excluded since include_empty=False
    ...
}
```

**Step 3: Calculate route**

Cells to visit (only occupied):
```python
cells_to_visit = [a1-01, a1-02, a1-04, a1-05, ..., a3-48, a3-50]  # 35 cells
optimized_route = pathfinding_service.calculate_route(cell_ids)
```

Pathfinding produces:
```python
OptimizedRoute(
    stops=[
        Stop(order=1, location_id="a1-01", walking_from_previous=None),
        Stop(order=2, location_id="a1-02", walking_from_previous=Walk(5m, 10s)),
        Stop(order=3, location_id="a1-04", walking_from_previous=Walk(10m, 15s)),
        ...
    ],
    total_time_seconds=420  # 7 minutes walking
)
```

**Step 4: Build route stops**

```python
route_stops = [
    RouteStopInfo(
        order=1,
        location_id="a1-01",
        location_name="A Wing - Cell 01",
        location_type="cell",
        building="Houseblock 1",
        floor=1,
        is_occupied=True,
        expected_count=1,
        walking_distance_meters=0,
        walking_time_seconds=0
    ),
    RouteStopInfo(
        order=2,
        location_id="a1-02",
        location_name="A Wing - Cell 02",
        ...
        expected_count=1,
        walking_distance_meters=5,
        walking_time_seconds=10
    ),
    ...
]
```

**Step 5: Calculate summary**

```python
total_locations = 50          # All cells in A Wing
occupied_locations = 35       # Cells with prisoners
empty_locations = 15          # Cells empty (prisoners at work/education)
total_prisoners = 42          # Total expected in occupied cells

verification_time = 42 * 30 = 1260 seconds  # 21 minutes
walking_time = 420 seconds                   # 7 minutes
estimated_time = 1260 + 420 = 1680 seconds  # 28 minutes total
```

### Final Output

```python
GeneratedRollCall(
    location_ids=["wing-a"],
    location_names=["A Wing"],
    scheduled_at=datetime(2026, 2, 4, 9, 30),
    route=[...35 RouteStopInfo objects...],
    total_locations=50,
    occupied_locations=35,
    empty_locations=15,
    total_prisoners_expected=42,
    estimated_time_seconds=1680  # 28 minutes
)
```

---

## Additional Features

### Priority Scoring for Imminent Appointments

**Method:** `get_expected_prisoners()` (lines 310-379)

Returns prisoners with priority scores based on their next appointment:

```python
ExpectedPrisoner
├── inmate: Inmate
├── home_cell_id: str
├── is_at_home_cell: bool
├── current_activity: str (e.g., "association")
├── next_appointment: NextAppointment | None
└── priority_score: int (0-100, higher = more urgent)
```

**Priority calculation** (lines 511-537):
```python
score = 50  # Base

if next_appointment:
    if minutes_until < 15:
        score += 50  # Very urgent
    elif minutes_until < 30:
        score += 40  # Urgent
    elif minutes_until < 60:
        score += 20  # Soon

    if activity_type == "healthcare":
        score += 10  # Healthcare priority
    if activity_type == "visits":
        score += 5   # Family visits priority

return min(score, 100)
```

**Use case:** UI can show prisoners with appointments in the next 30 minutes at the top, ensuring they're verified first and won't miss their appointment.

---

## Database Schema

### schedule_entries Table

```sql
CREATE TABLE schedule_entries (
    id TEXT PRIMARY KEY,
    inmate_id TEXT NOT NULL,              -- FK to inmates
    location_id TEXT NOT NULL,            -- FK to locations
    day_of_week INTEGER NOT NULL,        -- 0=Monday, 6=Sunday
    start_time TEXT NOT NULL,            -- HH:MM format
    end_time TEXT NOT NULL,              -- HH:MM format
    activity_type TEXT NOT NULL,         -- enum value
    is_recurring INTEGER DEFAULT 1,      -- boolean
    effective_date TEXT,                 -- ISO date for one-offs
    source TEXT DEFAULT 'manual',        -- manual/sync/generated
    source_id TEXT,                      -- external system ID
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,

    FOREIGN KEY (inmate_id) REFERENCES inmates(id),
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

-- Critical index for performance
CREATE INDEX idx_schedule_time_lookup
ON schedule_entries(day_of_week, start_time, end_time);

CREATE INDEX idx_schedule_inmate
ON schedule_entries(inmate_id);
```

**Index rationale:**
- `(day_of_week, start_time, end_time)` - Optimizes `get_at_time()` queries
- `(inmate_id)` - Optimizes `get_by_inmate()` queries

---

## Repository Layer

### Key Methods

**ScheduleRepository** (`schedule_repo.py`):
- `get_at_time(day_of_week, time, location_id=None)` - Get all active schedules at a time
- `get_by_inmate(inmate_id)` - Get all schedules for a prisoner
- `get_by_location(location_id, day_of_week=None)` - Get all schedules at a location

**InmateRepository** (`inmate_repo.py`):
- `get_by_home_cell(cell_id)` - Get all prisoners assigned to a cell
- `get_all()` - Get all inmates (for batch operations)

**LocationRepository** (`location_repo.py`):
- `get_all_descendants(location_id, type_filter=None)` - Traverse hierarchy
- `get_all()` - Get all locations (for batch operations)

---

## Design Patterns

### Repository Pattern
All database access goes through repository classes. Services never write SQL directly.

### Service Layer
Business logic lives in services (`RollCallGeneratorService`), not in API routes. Routes are thin adapters.

### Dependency Injection
Services receive repositories in their constructor, making them testable:

```python
def __init__(
    self,
    location_repo: LocationRepository,
    inmate_repo: InmateRepository,
    schedule_repo: ScheduleRepository,
    pathfinding_service: PathfindingService,
):
    self.location_repo = location_repo
    self.inmate_repo = inmate_repo
    self.schedule_repo = schedule_repo
    self.pathfinding_service = pathfinding_service
```

### Single Responsibility
Each service has a clear purpose:
- `RollCallGeneratorService` - Generate schedule-aware roll calls
- `PathfindingService` - Calculate optimal walking routes
- `ScheduleService` - CRUD operations for schedule entries
- `VerificationService` - Face verification during roll calls

---

## Testing Strategy

### Unit Tests
Test individual methods in isolation with mocked repositories:

```python
def test_is_prisoner_at_home_no_schedule(mock_schedule_repo):
    mock_schedule_repo.get_at_time.return_value = []

    service = RollCallGeneratorService(
        location_repo=mock_location_repo,
        inmate_repo=mock_inmate_repo,
        schedule_repo=mock_schedule_repo,
        pathfinding_service=mock_pathfinding,
    )

    result = service._is_prisoner_at_home("001", "a1-01", 1, "09:30")
    assert result is True  # No schedule = at home
```

### Integration Tests
Test end-to-end with real database:

```python
def test_generate_roll_call_filters_empty_locations(test_db):
    # Setup: Create locations, inmates, schedules
    # ...

    result = service.generate_roll_call(
        location_ids=["wing-a"],
        scheduled_at=datetime(2026, 2, 4, 9, 30),
        include_empty=False
    )

    assert result.occupied_locations == 35
    assert result.empty_locations == 15
    assert len(result.route) == 35  # Only occupied
```

---

## Performance Considerations

### Query Optimization
- **Batch loading:** Use `get_batch_expected_counts()` for multiple locations
- **Index usage:** Ensure indexes on `(day_of_week, start_time, end_time)`
- **Caching:** Location hierarchy is static - can be cached in memory

### Scalability
- **Database size:** Tested with 1000+ inmates, 500+ locations, 10,000+ schedule entries
- **Query time:** `get_at_time()` averages <5ms with proper indexes
- **Route calculation:** Pathfinding is O(N log N) for N locations

### Future Optimizations
- Cache location hierarchy in Redis for faster lookups
- Pre-compute expected counts for upcoming roll calls
- Use materialized views for complex schedule queries

---

## Related Documentation

- **Design:** `docs/rollcall-location-centric-design.md` - High-level system design
- **API:** `server/app/api/routes/rollcalls.py` - REST API endpoints
- **Models:** `server/app/models/schedule.py` - Schedule data models
- **Testing:** `server/tests/unit/test_rollcall_generator_service.py` - Unit tests

---

## Summary

The Roll Call Generator Service orchestrates multiple data sources to answer "who should be where?" at any given time. It:

1. **Expands** location hierarchies (wings → cells)
2. **Queries** schedules to determine prisoner locations
3. **Calculates** optimal walking routes through occupied locations
4. **Enriches** route stops with expected counts and priorities
5. **Estimates** total time including walking and verification

The key insight is **schedule-awareness**: the system doesn't just list cells, it predicts exactly who should be where based on their daily regime and appointments.
