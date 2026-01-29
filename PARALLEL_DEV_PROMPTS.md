# Parallel Developer Task Prompts

This document contains independent task prompts that can be worked on in parallel by different developers. Each prompt is self-contained with context, acceptance criteria, and testing requirements.

---

## PROMPT 1: Schedule System (Backend) - SEQUENTIAL TASK

**Estimated Effort:** 2-3 days
**Prerequisites:** None (uses existing patterns)
**Files to create/modify:**
- `server/app/models/schedule.py`
- `server/app/db/repositories/schedule_repo.py`
- `server/app/services/schedule_service.py`
- `server/app/api/routes/schedules.py`
- `server/migrations/004_schedule_entries.sql`
- `server/tests/unit/test_schedule_*.py`

### Context
The system needs to track prisoner schedules (work assignments, healthcare appointments, legal visits, etc.) to enable schedule-aware roll call generation. The RollCallGeneratorService already expects ScheduleRepository to exist.

### Requirements

#### 5.1 Schedule Data Model
Create Pydantic models and database schema:

**Models needed (app/models/schedule.py):**
```python
class ActivityType(str, Enum):
    WORK = "work"
    HEALTHCARE = "healthcare"
    LEGAL = "legal"
    EDUCATION = "education"
    RECREATION = "recreation"
    MEAL = "meal"
    LOCKUP = "lockup"
    FREE_TIME = "free_time"

class ScheduleEntry(BaseModel):
    id: str
    inmate_id: str
    location_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # HH:MM format
    end_time: str
    activity_type: ActivityType
    notes: str = ""
    created_at: datetime
    updated_at: datetime

class ScheduleEntryCreate(BaseModel):
    inmate_id: str
    location_id: str
    day_of_week: int
    start_time: str
    end_time: str
    activity_type: ActivityType
    notes: str = ""
```

**Database migration (migrations/004_schedule_entries.sql):**
```sql
CREATE TABLE schedule_entries (
    id TEXT PRIMARY KEY,
    inmate_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    day_of_week INTEGER NOT NULL CHECK(day_of_week BETWEEN 0 AND 6),
    start_time TEXT NOT NULL,  -- HH:MM format
    end_time TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    notes TEXT DEFAULT '',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    FOREIGN KEY (inmate_id) REFERENCES inmates(id) ON DELETE CASCADE,
    FOREIGN KEY (location_id) REFERENCES locations(id)
);

CREATE INDEX idx_schedule_inmate ON schedule_entries(inmate_id);
CREATE INDEX idx_schedule_location ON schedule_entries(location_id);
CREATE INDEX idx_schedule_day ON schedule_entries(day_of_week);
```

#### 5.2 Schedule Repository
Follow the repository pattern established in `app/db/repositories/inmate_repo.py`:

```python
class ScheduleRepository:
    def __init__(self, conn):
        self.conn = conn

    def create(self, entry: ScheduleEntryCreate) -> ScheduleEntry:
        """Create new schedule entry."""
        pass

    def get_by_id(self, entry_id: str) -> ScheduleEntry | None:
        """Get schedule entry by ID."""
        pass

    def get_by_inmate(self, inmate_id: str) -> list[ScheduleEntry]:
        """Get all schedule entries for an inmate."""
        pass

    def get_by_location(self, location_id: str) -> list[ScheduleEntry]:
        """Get all schedule entries for a location."""
        pass

    def get_active_at(self, inmate_id: str, check_time: datetime) -> ScheduleEntry | None:
        """Get the active schedule entry for an inmate at a specific time."""
        # Extract day_of_week and time from check_time
        # Query for matching day_of_week and time between start_time and end_time
        pass

    def update(self, entry_id: str, update: ScheduleEntryUpdate) -> ScheduleEntry:
        """Update schedule entry."""
        pass

    def delete(self, entry_id: str) -> bool:
        """Delete schedule entry."""
        pass

    def get_conflicts(self, inmate_id: str, day: int, start: str, end: str, exclude_id: str | None = None) -> list[ScheduleEntry]:
        """Find conflicting schedule entries for validation."""
        pass
```

#### 5.3 Schedule Service
Create business logic layer:

```python
class ScheduleService:
    def __init__(self, schedule_repo: ScheduleRepository, inmate_repo: InmateRepository, location_repo: LocationRepository):
        self.schedule_repo = schedule_repo
        self.inmate_repo = inmate_repo
        self.location_repo = location_repo

    def create_schedule_entry(self, entry: ScheduleEntryCreate) -> ScheduleEntry:
        """Create a new schedule entry with validation."""
        # Validate inmate exists
        # Validate location exists
        # Check for conflicts
        # Create entry
        pass

    def get_inmate_schedule(self, inmate_id: str) -> list[ScheduleEntry]:
        """Get full week schedule for an inmate."""
        pass

    def get_location_schedule(self, location_id: str) -> list[ScheduleEntry]:
        """Get all scheduled activities at a location."""
        pass

    def update_schedule_entry(self, entry_id: str, update: ScheduleEntryUpdate) -> ScheduleEntry:
        """Update schedule entry with conflict validation."""
        pass

    def delete_schedule_entry(self, entry_id: str) -> bool:
        """Delete schedule entry."""
        pass
```

#### 5.4 Schedule API Endpoints
Create REST API following pattern in `app/api/routes/inmates.py`:

```python
router = APIRouter()

@router.post("/schedules", response_model=ScheduleEntry, status_code=201)
async def create_schedule_entry(...)

@router.get("/schedules/{entry_id}", response_model=ScheduleEntry)
async def get_schedule_entry(...)

@router.put("/schedules/{entry_id}", response_model=ScheduleEntry)
async def update_schedule_entry(...)

@router.delete("/schedules/{entry_id}", status_code=204)
async def delete_schedule_entry(...)

@router.get("/schedules/inmate/{inmate_id}", response_model=list[ScheduleEntry])
async def get_inmate_schedules(...)

@router.get("/schedules/location/{location_id}", response_model=list[ScheduleEntry])
async def get_location_schedules(...)
```

### Acceptance Criteria
1. All models pass validation tests
2. Database migration runs successfully
3. Repository has 100% test coverage (15+ tests)
4. Service has conflict detection tests
5. API endpoints return correct status codes
6. All integration tests pass
7. ScheduleRepository is compatible with RollCallGeneratorService expectations

### Testing Requirements
- Unit tests for each repository method
- Service layer tests for conflict detection
- Integration tests for API endpoints
- Test time parsing and day-of-week logic
- Test foreign key constraints

### References
- Existing pattern: `app/db/repositories/inmate_repo.py`
- Service pattern: `app/services/rollcall_service.py`
- API pattern: `app/api/routes/inmates.py`
- Already consumes this: `app/services/rollcall_generator_service.py` (line 34)

---

## PROMPT 2: Audit Service (Backend)

**Estimated Effort:** 1 day
**Prerequisites:** None
**Files to create:**
- `server/app/services/audit_service.py`
- `server/app/db/repositories/audit_repo.py`
- `server/migrations/005_audit_log.sql`
- `server/tests/unit/test_audit_service.py`

### Context
The system needs audit logging for security and compliance. All roll call operations, verification overrides, and administrative actions should be logged.

### Requirements

**Database schema:**
```sql
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    user_id TEXT NOT NULL,
    action TEXT NOT NULL,  -- 'roll_call_start', 'verification', 'manual_override', etc.
    entity_type TEXT NOT NULL,  -- 'roll_call', 'inmate', 'location', etc.
    entity_id TEXT NOT NULL,
    details TEXT,  -- JSON blob with additional context
    ip_address TEXT,
    user_agent TEXT
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_user ON audit_log(user_id);
CREATE INDEX idx_audit_entity ON audit_log(entity_type, entity_id);
```

**Service interface:**
```python
class AuditService:
    def log_action(
        self,
        user_id: str,
        action: str,
        entity_type: str,
        entity_id: str,
        details: dict | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> None:
        """Log an auditable action."""
        pass

    def get_entity_history(self, entity_type: str, entity_id: str) -> list[AuditEntry]:
        """Get audit trail for a specific entity."""
        pass

    def get_user_actions(self, user_id: str, start: datetime, end: datetime) -> list[AuditEntry]:
        """Get all actions by a user in a time range."""
        pass

    def export_logs(self, start: datetime, end: datetime, format: str = "csv") -> str:
        """Export audit logs for a time period."""
        pass
```

### Acceptance Criteria
1. Audit entries are immutable (no update/delete)
2. Service handles JSON serialization for details field
3. Repository tests cover all query methods
4. Export function produces valid CSV
5. All tests pass with >80% coverage

### Testing Requirements
- Test log creation
- Test queries by entity, user, time range
- Test JSON serialization/deserialization
- Test CSV export format

---

## PROMPT 3: Authentication Middleware (Backend)

**Estimated Effort:** 1 day
**Prerequisites:** None
**Files to create:**
- `server/app/api/middleware/auth.py`
- `server/tests/unit/test_auth_middleware.py`
- `server/tests/integration/test_auth_endpoints.py`

### Context
The API needs authentication via API keys. The system runs on a closed network but still needs to prevent unauthorized access.

### Requirements

**Middleware implementation:**
```python
class APIKeyAuth:
    """API Key authentication middleware."""

    def __init__(self, api_keys: set[str]):
        self.api_keys = api_keys

    async def __call__(self, request: Request, call_next):
        # Extract API key from header
        api_key = request.headers.get("X-API-Key")

        # Validate key
        if api_key not in self.api_keys:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or missing API key"}
            )

        # Add user_id to request state for audit logging
        request.state.user_id = self._get_user_for_key(api_key)

        response = await call_next(request)
        return response
```

**Configuration:**
```python
# In app/config.py
class Settings(BaseSettings):
    api_keys: str = "dev-key-1,dev-key-2"  # Comma-separated

    def get_api_keys(self) -> set[str]:
        return set(self.api_keys.split(","))
```

**Exempt endpoints:**
- `/docs`
- `/redoc`
- `/openapi.json`
- `/health`

### Acceptance Criteria
1. Middleware rejects requests without valid API key
2. Health endpoint remains unauthenticated
3. API docs remain accessible
4. User ID is attached to request for audit logging
5. All protected endpoints require authentication
6. Tests cover valid, invalid, and missing keys

### Testing Requirements
- Test valid API key access
- Test invalid API key rejection
- Test missing API key rejection
- Test exempt endpoints
- Integration test with real endpoints

---

## PROMPT 4: Global Error Handling (Backend)

**Estimated Effort:** 1 day
**Prerequisites:** None
**Files to modify:**
- `server/app/main.py`
- `server/app/api/errors.py` (create)
- `server/tests/integration/test_error_handling.py`

### Context
The API needs consistent error responses and proper HTTP status codes. All exceptions should be caught and formatted consistently.

### Requirements

**Custom exceptions (app/api/errors.py):**
```python
class APIError(Exception):
    """Base API error."""
    def __init__(self, message: str, status_code: int = 400):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

class NotFoundError(APIError):
    def __init__(self, resource: str, id: str):
        super().__init__(f"{resource} {id} not found", status_code=404)

class ValidationError(APIError):
    def __init__(self, message: str):
        super().__init__(message, status_code=400)

class ConflictError(APIError):
    def __init__(self, message: str):
        super().__init__(message, status_code=409)

class UnauthorizedError(APIError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, status_code=401)
```

**Global error handlers (app/main.py):**
```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

app = FastAPI()

@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.__class__.__name__,
            "message": exc.message,
            "path": request.url.path,
        }
    )

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={
            "error": "ValueError",
            "message": str(exc),
            "path": request.url.path,
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    # Log the error
    logger.exception(f"Unhandled exception: {exc}")

    return JSONResponse(
        status_code=500,
        content={
            "error": "InternalServerError",
            "message": "An unexpected error occurred",
            "path": request.url.path,
        }
    )
```

### Acceptance Criteria
1. All errors return consistent JSON format
2. 404 errors for missing resources
3. 400 errors for validation failures
4. 500 errors for unexpected exceptions
5. Error responses include error type and message
6. Sensitive error details not exposed in production

### Testing Requirements
- Test each custom exception type
- Test ValueError handling
- Test unexpected exception handling
- Test error response format
- Integration tests with real endpoints

---

## PROMPT 5: Demo Data Generator (Backend)

**Estimated Effort:** 1-2 days
**Prerequisites:** Schedule system complete (Prompt 1)
**Files to create:**
- `server/scripts/generate_schedules.py`
- `server/tests/unit/test_schedule_generator.py`

### Context
Need realistic demo data showing 2 weeks of prisoner schedules with varied patterns (work, healthcare, meals, lockup) for demonstration purposes.

### Requirements

**Script features:**
```python
def generate_schedules(
    inmates: list[Inmate],
    locations: list[Location],
    weeks: int = 2
) -> list[ScheduleEntry]:
    """Generate realistic prisoner schedules.

    Patterns to implement:
    - Daily lockup: 22:00-07:00 (all inmates, in home cells)
    - Meals: Breakfast 07:30-08:30, Lunch 12:00-13:00, Dinner 17:30-18:30
    - Work assignments: 09:00-12:00 and 14:00-17:00 (weekdays only, 60% of inmates)
    - Education: 09:00-11:00 or 14:00-16:00 (20% of inmates, 2-3 days/week)
    - Healthcare: Random appointments (5% of inmates per week)
    - Recreation: 13:00-14:00 daily (in gym/yard)
    - Legal visits: Random (2% of inmates per week, weekdays only)
    - Free time: Gaps between scheduled activities

    Individual variations:
    - Healthcare frequency varies by inmate
    - Work locations distributed across workshops
    - Some inmates have education + work (different days)
    - Weekend schedules: meals, recreation, free time only
    """
    pass

def assign_work_locations(inmates: list[Inmate], work_locations: list[Location]) -> dict[str, str]:
    """Distribute inmates across work locations."""
    pass

def schedule_random_appointments(inmates: list[Inmate], activity_type: ActivityType, percentage: float, locations: list[Location]) -> list[ScheduleEntry]:
    """Schedule random appointments (healthcare, legal)."""
    pass
```

### Acceptance Criteria
1. Generates valid schedule entries
2. No scheduling conflicts per inmate
3. Realistic time ranges (no 3am work assignments)
4. Weekend vs weekday patterns differ
5. Individual variation (not all inmates identical)
6. Works with existing seed data
7. Output can be validated by ScheduleService

### Testing Requirements
- Test conflict detection
- Test time range validation
- Test weekday/weekend differences
- Test distribution across locations
- Test percentage-based scheduling

---

## PROMPT 6: Roll Call List Page (Web UI)

**Estimated Effort:** 1 day
**Prerequisites:** None (API exists)
**Files to create:**
- `web-ui/src/routes/rollcalls/+page.svelte`
- `web-ui/src/routes/rollcalls/+page.ts` (load function)
- `web-ui/tests/rollcalls-list.test.ts`

### Context
Officers need to view all roll calls (past, present, future) with status and quick actions.

### Requirements

**Page features:**
- Display all roll calls in table/list
- Show: name, status, scheduled time, officer, location count
- Status badges: scheduled (blue), in_progress (yellow), completed (green), cancelled (red)
- Quick actions: Start, View, Delete
- Filter by status dropdown
- Sort by date (newest first default)
- Link to create new roll call
- Click row to view details

**API integration:**
```typescript
// Load function
export async function load({ fetch }) {
  const response = await fetch('http://localhost:8000/rollcalls');
  const rollcalls = await response.json();
  return { rollcalls };
}
```

**Component structure:**
```svelte
<script lang="ts">
  import type { PageData } from './$types';
  export let data: PageData;

  let statusFilter: string = 'all';

  $: filteredRollCalls = data.rollcalls.filter(rc =>
    statusFilter === 'all' || rc.status === statusFilter
  );
</script>

<div class="container mx-auto p-4">
  <div class="flex justify-between items-center mb-4">
    <h1 class="text-2xl font-bold">Roll Calls</h1>
    <a href="/rollcalls/new" class="btn btn-primary">Create Roll Call</a>
  </div>

  <select bind:value={statusFilter} class="mb-4">
    <option value="all">All Statuses</option>
    <option value="scheduled">Scheduled</option>
    <option value="in_progress">In Progress</option>
    <option value="completed">Completed</option>
    <option value="cancelled">Cancelled</option>
  </select>

  <table class="w-full">
    <!-- Table implementation -->
  </table>
</div>
```

### Acceptance Criteria
1. Displays all roll calls from API
2. Status filter works correctly
3. Status badges show correct colors
4. Quick actions functional
5. Responsive design
6. Loading state shown
7. Error handling for API failures

### Testing Requirements
- Unit test for filtering logic
- Test status badge rendering
- Test action buttons
- Mock API responses

**Reference:** See `web-ui/src/routes/prisoners/+page.svelte` for existing list pattern

---

## PROMPT 7: Create Roll Call Page (Web UI)

**Estimated Effort:** 1-2 days
**Prerequisites:** None (generate endpoint exists)
**Files to create:**
- `web-ui/src/routes/rollcalls/new/+page.svelte`
- `web-ui/src/routes/rollcalls/new/+page.ts`
- `web-ui/src/lib/components/LocationPicker.svelte`
- `web-ui/tests/rollcalls-create.test.ts`

### Context
Officers need a UI to create roll calls by selecting locations and reviewing the generated route.

### Requirements

**Page workflow:**
1. Officer selects one or more locations (tree picker with checkboxes)
2. Officer selects scheduled time
3. Officer clicks "Generate Route"
4. System calls POST /rollcalls/generate and shows preview
5. Preview shows: route stops, expected counts, estimated time
6. Officer can adjust (include_empty flag)
7. Officer clicks "Create Roll Call" to confirm
8. System calls POST /rollcalls with route data

**Location picker component:**
```svelte
<!-- LocationPicker.svelte -->
<script lang="ts">
  export let selectedLocationIds: string[] = [];
  export let locations: Location[];

  // Group by hierarchy (houseblock -> wing -> landing -> cell)
  // Render as expandable tree with checkboxes
  // Handle parent selection (check all children)
</script>

<div class="location-tree">
  <!-- Tree structure with checkboxes -->
</div>
```

**Form structure:**
```svelte
<script lang="ts">
  let selectedLocationIds: string[] = [];
  let scheduledAt: string = '';
  let includeEmpty: boolean = true;
  let generatedRoute: any = null;

  async function generateRoute() {
    const response = await fetch('http://localhost:8000/rollcalls/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        location_ids: selectedLocationIds,
        scheduled_at: scheduledAt,
        include_empty: includeEmpty,
      })
    });
    generatedRoute = await response.json();
  }

  async function createRollCall() {
    const response = await fetch('http://localhost:8000/rollcalls', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        name: `Roll Call - ${new Date(scheduledAt).toLocaleString()}`,
        status: 'scheduled',
        scheduled_at: scheduledAt,
        ordered_locations: generatedRoute.route.map(r => r.location_id),
        created_by: 'officer-001',
      })
    });

    if (response.ok) {
      goto('/rollcalls');
    }
  }
</script>
```

### Acceptance Criteria
1. Location tree picker works with hierarchy
2. Generate route API call succeeds
3. Route preview shows all stops
4. Summary shows expected counts and time
5. Create roll call saves to database
6. Redirects to list after creation
7. Validation for required fields
8. Error handling for API failures

### Testing Requirements
- Test location selection
- Test route generation
- Test roll call creation
- Mock API responses
- Test validation errors

---

## PROMPT 8: Active Roll Call Page (Web UI)

**Estimated Effort:** 2-3 days
**Prerequisites:** None
**Files to create:**
- `web-ui/src/routes/rollcalls/[id]/active/+page.svelte`
- `web-ui/src/routes/rollcalls/[id]/active/+page.ts`
- `web-ui/src/lib/components/VerificationCamera.svelte`
- `web-ui/src/lib/stores/rollCallStore.ts`
- `web-ui/tests/active-rollcall.test.ts`

### Context
Officers need a page to conduct an active roll call with continuous webcam verification.

### Requirements

**Page structure:**
1. Top: Current location, progress (5/20 cells)
2. Middle: Live webcam feed
3. Bottom: Expected prisoners list, verification results
4. Navigation: Previous/Next location buttons

**Verification flow:**
1. Page loads current route stop
2. Camera starts automatically
3. Officer points camera at prisoner
4. System continuously calls POST /verify/quick
5. On match: Show green checkmark, auto-mark verified
6. On no-match: Show prisoner selector for manual override
7. Officer can skip to next location
8. Complete button when all locations done

**Camera component:**
```svelte
<!-- VerificationCamera.svelte -->
<script lang="ts">
  export let onVerification: (result: VerificationResult) => void;

  let videoElement: HTMLVideoElement;
  let stream: MediaStream;
  let isScanning = false;

  async function startCamera() {
    stream = await navigator.mediaDevices.getUserMedia({ video: true });
    videoElement.srcObject = stream;
  }

  async function captureAndVerify() {
    if (!isScanning) return;

    // Capture frame from video
    const canvas = document.createElement('canvas');
    canvas.width = videoElement.videoWidth;
    canvas.height = videoElement.videoHeight;
    canvas.getContext('2d').drawImage(videoElement, 0, 0);

    const blob = await new Promise(resolve => canvas.toBlob(resolve));

    // Send to API
    const formData = new FormData();
    formData.append('image', blob);

    const response = await fetch('http://localhost:8000/verify/quick', {
      method: 'POST',
      body: formData,
    });

    const result = await response.json();
    onVerification(result);

    // Continue scanning
    setTimeout(captureAndVerify, 1000);
  }

  onMount(() => {
    startCamera();
    isScanning = true;
    captureAndVerify();
  });

  onDestroy(() => {
    isScanning = false;
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
    }
  });
</script>

<video bind:this={videoElement} autoplay class="w-full rounded-lg"></video>
```

**Store for state management:**
```typescript
// rollCallStore.ts
import { writable } from 'svelte/store';

export const rollCallStore = writable({
  currentStopIndex: 0,
  verifications: [],
  rollCall: null,
});

export function nextLocation() {
  rollCallStore.update(state => ({
    ...state,
    currentStopIndex: state.currentStopIndex + 1,
  }));
}

export function recordVerification(verification) {
  rollCallStore.update(state => ({
    ...state,
    verifications: [...state.verifications, verification],
  }));
}
```

### Acceptance Criteria
1. Camera starts automatically
2. Continuous scanning works
3. Verification results displayed in real-time
4. Progress updates correctly
5. Navigation between locations works
6. Manual override flow functional
7. Complete button finalizes roll call
8. All verifications saved via API

### Testing Requirements
- Mock camera API
- Test verification flow
- Test navigation
- Test progress tracking
- Test manual override

**Reference:** See `web-ui/src/routes/prisoners/[id]/enroll/+page.svelte` for camera pattern

---

## PROMPT 9: Reusable UI Components (Web UI)

**Estimated Effort:** 1 day
**Prerequisites:** None
**Files to create:**
- `web-ui/src/lib/components/StatCard.svelte`
- `web-ui/src/lib/components/PrisonerCard.svelte`
- `web-ui/src/lib/components/LocationCard.svelte`
- `web-ui/src/lib/components/StatusBadge.svelte`
- `web-ui/tests/components/*.test.ts`

### Context
Multiple pages need consistent card components for displaying stats, prisoners, and locations.

### Requirements

**StatCard:**
```svelte
<script lang="ts">
  export let label: string;
  export let value: number | string;
  export let icon: string = '';
  export let color: 'blue' | 'green' | 'red' | 'yellow' = 'blue';
</script>

<div class="stat-card bg-white p-4 rounded shadow border-l-4 border-{color}-500">
  <div class="flex items-center justify-between">
    <div>
      <p class="text-gray-600 text-sm">{label}</p>
      <p class="text-2xl font-bold">{value}</p>
    </div>
    {#if icon}
      <span class="text-4xl">{icon}</span>
    {/if}
  </div>
</div>
```

**PrisonerCard:**
```svelte
<script lang="ts">
  export let inmate: Inmate;
  export let showEnrollment: boolean = true;
</script>

<div class="prisoner-card bg-white p-4 rounded shadow hover:shadow-lg transition">
  <div class="flex justify-between items-start">
    <div>
      <h3 class="font-bold">{inmate.first_name} {inmate.last_name}</h3>
      <p class="text-sm text-gray-600">{inmate.inmate_number}</p>
      <p class="text-sm">{inmate.cell_block}-{inmate.cell_number}</p>
    </div>
    {#if showEnrollment}
      <StatusBadge status={inmate.is_enrolled ? 'enrolled' : 'not_enrolled'} />
    {/if}
  </div>
</div>
```

**LocationCard:**
```svelte
<script lang="ts">
  export let location: Location;
  export let showCapacity: boolean = false;
</script>

<div class="location-card bg-white p-4 rounded shadow">
  <h3 class="font-bold">{location.name}</h3>
  <p class="text-sm text-gray-600">{location.type}</p>
  {#if showCapacity && location.capacity}
    <p class="text-sm">Capacity: {location.capacity}</p>
  {/if}
</div>
```

**StatusBadge:**
```svelte
<script lang="ts">
  export let status: string;

  const colorMap = {
    scheduled: 'blue',
    in_progress: 'yellow',
    completed: 'green',
    cancelled: 'red',
    enrolled: 'green',
    not_enrolled: 'gray',
  };

  const color = colorMap[status] || 'gray';
</script>

<span class="badge bg-{color}-100 text-{color}-800 px-2 py-1 rounded text-xs">
  {status.replace('_', ' ')}
</span>
```

### Acceptance Criteria
1. All components render correctly
2. Props work as expected
3. Tailwind classes apply correctly
4. Components are reusable
5. TypeScript types defined
6. Tests cover all variants

### Testing Requirements
- Test each component with different props
- Test conditional rendering
- Snapshot tests for visual regression

---

## PROMPT 10: Deployment Scripts (Backend)

**Estimated Effort:** 1-2 days
**Prerequisites:** None
**Files to create:**
- `server/scripts/setup_hotspot.sh`
- `server/scripts/seed_data.py`
- `server/scripts/export_audit.py`
- `server/docs/DEPLOYMENT.md`

### Context
The system needs to run on a laptop configured as a WiFi hotspot. Scripts needed for initial setup and data export.

### Requirements

**setup_hotspot.sh:**
```bash
#!/bin/bash
# Configure laptop as WiFi hotspot for closed network

# Check for Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "Error: This script requires Linux"
    exit 1
fi

# Install dependencies
sudo apt-get update
sudo apt-get install -y hostapd dnsmasq

# Configure hostapd
sudo cat > /etc/hostapd/hostapd.conf <<EOF
interface=wlan0
driver=nl80211
ssid=PrisonRollCall
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=RollCall2024
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
EOF

# Configure dnsmasq
sudo cat > /etc/dnsmasq.conf <<EOF
interface=wlan0
dhcp-range=192.168.50.10,192.168.50.100,255.255.255.0,24h
EOF

# Enable IP forwarding
sudo sysctl -w net.ipv4.ip_forward=1

# Start services
sudo systemctl start hostapd
sudo systemctl start dnsmasq

echo "Hotspot configured. SSID: PrisonRollCall"
```

**seed_data.py:**
```python
"""Seed database with demo data."""
import sqlite3
from pathlib import Path
from app.db.database import get_connection
from app.db.repositories.inmate_repo import InmateRepository
from app.db.repositories.location_repo import LocationRepository

def seed_hmp_oakwood(db_path: str):
    """Seed database with HMP Oakwood structure."""
    conn = get_connection(db_path)

    location_repo = LocationRepository(conn)
    inmate_repo = InmateRepository(conn)

    # Create location hierarchy
    # Create inmates
    # Assign inmates to cells

    print(f"Seeded {inmate_count} inmates and {location_count} locations")

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else "prison_rollcall.db"
    seed_hmp_oakwood(db_path)
```

**export_audit.py:**
```python
"""Export audit logs to CSV."""
import csv
from datetime import datetime
from app.services.audit_service import AuditService

def export_audit_logs(start_date: str, end_date: str, output_file: str):
    """Export audit logs to CSV."""
    audit_service = AuditService(...)

    logs = audit_service.get_logs(
        start=datetime.fromisoformat(start_date),
        end=datetime.fromisoformat(end_date)
    )

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'user_id', 'action', 'entity_type', 'entity_id', 'details'])
        writer.writeheader()
        writer.writerows([log.dict() for log in logs])

    print(f"Exported {len(logs)} audit logs to {output_file}")

if __name__ == "__main__":
    import sys
    export_audit_logs(sys.argv[1], sys.argv[2], sys.argv[3])
```

### Acceptance Criteria
1. Hotspot script works on Ubuntu/Debian
2. Seed script creates realistic demo data
3. Export script produces valid CSV
4. Documentation covers all scripts
5. Error handling for common issues
6. Scripts are idempotent where possible

### Testing Requirements
- Test seed script creates valid data
- Test export CSV format
- Manual testing for hotspot setup

---

## Task Dependencies

```
Independent (can start immediately):
- Prompt 2: Audit Service
- Prompt 3: Authentication Middleware
- Prompt 4: Global Error Handling
- Prompt 6: Roll Call List Page
- Prompt 9: Reusable UI Components
- Prompt 10: Deployment Scripts

Sequential:
- Prompt 1: Schedule System (5.1 → 5.2 → 5.3 → 5.4 in order)
  ↓
- Prompt 5: Demo Data Generator (needs Prompt 1 complete)

UI depends on API:
- Prompt 7: Create Roll Call Page (needs /rollcalls/generate - already exists)
- Prompt 8: Active Roll Call Page (needs /verify/quick - already exists)
```

## Recommended Parallel Execution Plan

**Week 1:**
- Developer 1: Prompt 1 (Schedule System - sequential)
- Developer 2: Prompt 2 + 3 + 4 (Audit + Auth + Errors)
- Developer 3: Prompt 6 + 7 (Roll Call List + Create)
- Developer 4: Prompt 9 + 10 (UI Components + Deployment)

**Week 2:**
- Developer 1: Prompt 5 (Demo Data Generator)
- Developer 2: Integration testing
- Developer 3: Prompt 8 (Active Roll Call)
- Developer 4: E2E testing

All developers should follow TDD workflow and run full test suite before committing.
