# Test Coverage Audit Prompt

## Context

You are auditing the test suite for a Prison Roll Call application (FastAPI backend + SvelteKit frontend). We recently discovered a gap where tests passed but production code failed.

**The Issue:**
- The `generate_schedules.py` script created database entries with 9 new `ActivityType` enum values
- The backend `ActivityType` enum only had 13 values defined
- Integration tests passed because they used hardcoded mock data instead of running the real data generation scripts
- When a user tried to create a rollcall in the UI, it failed with: `'healthcare_residence' is not a valid ActivityType`

**Why Tests Missed It:**
- Tests created fake rollcalls with `sample_route` fixtures containing hardcoded data
- Tests never ran `seed_hmp_oakwood.py` + `generate_schedules.py` to populate real data
- Tests didn't validate that data from scripts could be loaded by the application models
- **No integration test validated the full flow: seed → generate → query → use**

## Your Mission

Audit the entire test suite to find similar scenarios where tests might pass but production would fail.

## What to Look For

### Pattern 1: Mock Data vs Real Data Scripts

**Red Flag:** Tests use hardcoded fixtures instead of running real data generation/seeding scripts

**Questions to ask:**
1. Are there any Python scripts in `server/scripts/` that generate or seed data?
2. Do integration tests actually run these scripts, or do they use mock data?
3. Could the scripts create data that violates application constraints?
4. Are there enum values, validation rules, or schema constraints that could drift between scripts and models?

**Example locations to check:**
- `server/scripts/*.py` - Data generation scripts
- `tests/integration/*.py` - Integration tests
- `tests/fixtures/*.py` or `conftest.py` - Shared test fixtures
- Look for: `@pytest.fixture`, `def sample_*`, hardcoded dictionaries/objects

### Pattern 2: Database Enum Mismatches

**Red Flag:** Database can contain string values that don't exist in Python Enum definitions

**Questions to ask:**
1. Where are Enums defined? (`app/models/*.py`)
2. What database tables use these enum values as strings?
3. Are there any scripts that insert these values directly into the database?
4. Do repositories convert database strings to Enums when loading data?

**Example code pattern:**
```python
# This will fail if database has invalid enum value:
activity_type=ActivityType(row[6])
```

**Files to audit:**
- `app/models/*.py` - Enum definitions
- `app/db/repositories/*.py` - Look for `_row_to_model()` methods and enum conversions
- `server/scripts/*.py` - Database insert statements with string literals
- Database schema: `app/db/schema.py` or migration files

### Pattern 3: Missing End-to-End Tests

**Red Flag:** No tests that exercise the full user workflow from start to finish

**Questions to ask:**
1. What are the main user workflows (e.g., "create rollcall", "enroll prisoner face")?
2. Do tests cover the complete flow, or just individual API endpoints?
3. Are there tests that:
   - Seed the database with realistic data
   - Call multiple APIs in sequence as a user would
   - Validate that downstream operations work with upstream data?

**Example missing test:**
```python
def test_full_rollcall_creation_workflow():
    """Missing test that would have caught our bug"""
    # 1. Seed prison structure
    run_script("seed_hmp_oakwood.py")

    # 2. Generate schedules (with new activity types)
    run_script("generate_schedules.py")

    # 3. Query schedule data (this is where it would fail!)
    response = client.get("/api/v1/schedules")
    assert response.status_code == 200

    # 4. Create rollcall using schedule data
    response = client.post("/api/v1/rollcalls/generate", json={...})
    assert response.status_code == 200
```

### Pattern 4: Type System Gaps

**Red Flag:** Pydantic models don't validate all possible database states

**Questions to ask:**
1. Can the database contain values that would make Pydantic validation fail?
2. Are there database columns without NOT NULL constraints that Python code assumes are required?
3. Are there foreign key relationships that Python code assumes exist but aren't enforced?
4. Do JSON columns in the database match their TypedDict/Pydantic definitions?

**Example code to check:**
```python
class Location(BaseModel):
    parent_id: str | None  # Optional in Python
    # But code might assume: parent = locations.find(loc.parent_id)
    # This fails if parent was deleted but FK not enforced!
```

### Pattern 5: Web UI Integration Gaps

**Red Flag:** Backend tests pass but web UI calls fail

**Questions to ask:**
1. Are there `web-ui/src/lib/services/api.ts` functions that aren't tested?
2. Do any API calls in the web UI transform data before sending?
3. Are there type mismatches between TypeScript interfaces and Python models?
4. Do web UI tests mock API responses instead of calling real endpoints?

**Example locations:**
- `web-ui/src/lib/services/api.ts` - API client functions
- `web-ui/src/routes/**/__tests__/*.test.ts` - Frontend tests
- Look for: `vi.mock()`, `jest.mock()`, hardcoded API responses

## Specific Files to Audit

### High Priority

1. **Data Generation Scripts:**
   - `server/scripts/generate_schedules.py`
   - `server/scripts/seed_hmp_oakwood.py`
   - `server/scripts/seed_prison.py`
   - Any other `scripts/*.py` files

2. **Enum Definitions:**
   - `app/models/schedule.py` - ActivityType
   - `app/models/location.py` - LocationType
   - `app/models/rollcall.py` - RollCallStatus, RouteStopStatus
   - Look for any other `class *Type(str, Enum)`

3. **Repository Row Conversions:**
   - `app/db/repositories/schedule_repo.py` - `_row_to_model()`
   - `app/db/repositories/location_repo.py` - `_row_to_model()`
   - All `*_repo.py` files with enum conversions

4. **Integration Test Fixtures:**
   - `tests/conftest.py`
   - `tests/fixtures/*.py`
   - `tests/integration/test_rollcalls_api.py` - `sample_route` fixture
   - Look for any `@pytest.fixture` that creates mock data

### Medium Priority

5. **API Endpoints:**
   - `app/api/routes/rollcalls.py` - `/rollcalls/generate`, `/rollcalls/expected/batch-counts`
   - `app/api/routes/schedules.py`
   - All routes that query database and return models

6. **Web UI API Calls:**
   - `web-ui/src/lib/services/api.ts`
   - `web-ui/src/routes/rollcalls/new/+page.svelte` - getBatchExpectedCounts
   - Any page that calls backend APIs

7. **Type Definitions:**
   - `web-ui/src/lib/services/api.ts` - TypeScript interfaces
   - Compare with `app/models/*.py` - Python models

## Expected Output

For each issue found, provide:

### 1. Issue Summary
```
Title: [Clear description]
Severity: Critical | High | Medium | Low
Category: Mock Data Gap | Enum Mismatch | Missing E2E Test | Type Gap
```

### 2. Description
- What is the issue?
- Why is it a problem?
- How could it cause production failures?

### 3. Evidence
- File paths and line numbers
- Code snippets showing the issue
- Related test files that should catch it but don't

### 4. Reproduction Scenario
- Step-by-step how a user would trigger the bug
- Example: "User seeds data → generates schedules → creates rollcall → error"

### 5. Recommended Fix
- What tests should be added?
- What code should be changed?
- Prioritization (fix now vs later)

## Example Output Format

```markdown
## Issue #1: Location Type Enum Mismatch

**Severity:** High
**Category:** Enum Mismatch

### Description
The `seed_hmp_oakwood.py` script creates locations with `type="yard"` but the `LocationType`
enum only defines `YARD = "exercise_yard"`. This mismatch would cause validation errors when
the repository tries to convert database rows to models.

### Evidence
- File: `server/scripts/seed_hmp_oakwood.py:190`
  ```python
  create_location(conn, "Exercise Yard 1", "yard", capacity=150)
  ```
- File: `app/models/location.py:15`
  ```python
  class LocationType(str, Enum):
      YARD = "exercise_yard"  # Mismatch!
  ```
- File: `app/db/repositories/location_repo.py:85`
  ```python
  type=LocationType(row[2])  # This will fail!
  ```

### Reproduction
1. Run `python scripts/seed_hmp_oakwood.py`
2. Call `GET /api/v1/locations`
3. Error: `'yard' is not a valid LocationType`

### Why Tests Didn't Catch It
- `tests/integration/test_locations_api.py` uses `LocationCreate` which validates the enum
- No test that seeds data with script then queries it
- No test that loads all locations from database after seeding

### Recommended Fix
**Priority:** High (same pattern as the ActivityType bug)

1. Fix the enum definition or the script to match
2. Add integration test:
   ```python
   def test_can_load_all_seeded_locations(test_db):
       # Run seed script
       subprocess.run(["python", "scripts/seed_hmp_oakwood.py"])

       # Load all locations via repository
       conn = get_connection(test_db)
       repo = LocationRepository(conn)
       locations = repo.get_all()  # Should not raise ValueError
       assert len(locations) > 0
   ```
```

## Success Criteria

Your audit is complete when you have:

1. ✅ Reviewed all data generation scripts in `server/scripts/`
2. ✅ Checked all Enum definitions against database inserts
3. ✅ Identified all integration tests using mock data instead of real scripts
4. ✅ Found all `_row_to_model()` methods with enum conversions
5. ✅ Listed missing end-to-end tests for main user workflows
6. ✅ Compared TypeScript interfaces with Python models
7. ✅ Prioritized issues (Critical/High/Medium/Low)
8. ✅ Provided actionable test recommendations

## Starting Points

1. **Start with scripts:** Run `ls server/scripts/*.py` and examine each
2. **Find all enums:** Run `grep -r "class.*Enum" app/models/`
3. **Find row conversions:** Run `grep -r "_row_to_model" app/db/repositories/`
4. **Check fixtures:** Look at `tests/conftest.py` and search for `@pytest.fixture`
5. **List integration tests:** Run `ls tests/integration/*.py`

## Questions to Consider

- Are there other scripts like `generate_schedules.py` that create data?
- Are there database migrations that add columns without updating models?
- Are there admin interfaces that might create invalid data?
- Could data imported from external systems violate constraints?
- Are there CLI commands that bypass normal validation?

## Output Format

Create a report in this format:

```markdown
# Test Coverage Audit Report

## Executive Summary
- Total issues found: X
- Critical: X | High: X | Medium: X | Low: X
- Estimated effort to fix: X hours

## Critical Issues (Fix Immediately)
[List here]

## High Priority Issues (Fix This Sprint)
[List here]

## Medium Priority Issues (Fix Next Sprint)
[List here]

## Low Priority Issues (Backlog)
[List here]

## Recommended Test Additions
1. [Test description]
2. [Test description]

## Process Improvements
- [Suggestion 1]
- [Suggestion 2]
```

Good luck with your audit!
