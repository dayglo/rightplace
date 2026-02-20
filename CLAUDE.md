# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Prison Roll Call** is a face recognition system for inmate verification during facility roll calls. The system consists of:

- **FastAPI Server** (`server/`): ML-powered backend providing face detection, recognition, and inmate management
- **SvelteKit Web UI** (`web-ui/`): Customer demo interface for webcam-based verification
- **Future React Native Mobile App**: Planned native mobile client (not yet implemented)

The server runs on a laptop configured as a WiFi hotspot, creating a closed local network with no internet connectivity. Devices connect to this hotspot to perform roll call operations.

## Architecture

### Server (FastAPI + DeepFace)
```
server/app/
├── api/routes/          # REST API endpoints (health, inmates, locations, rollcalls, etc.)
├── db/repositories/     # Data access layer (InmateRepo, LocationRepo, EmbeddingRepo, etc.)
├── ml/                  # Face detection and recognition (DeepFace wrapper)
├── models/              # Pydantic schemas (Inmate, Location, RollCall, Verification, etc.)
└── services/            # Business logic layer (VerificationService, PathfindingService, etc.)
```

**Key Patterns:**
- **Repository Pattern**: All database access goes through repository classes in `app/db/repositories/`
- **Service Layer**: Business logic lives in `app/services/`, not in routes
- **Dependency Injection**: Routes receive dependencies (settings, session) via FastAPI DI
- **ML Isolation**: All ML code is encapsulated in `app/ml/` using DeepFace library

### Web UI (SvelteKit + Tailwind)
```
web-ui/src/
├── lib/                 # Components, stores, utilities
└── routes/              # SvelteKit file-based routing
```

**Key Technologies:**
- SvelteKit for SSR and routing
- Tailwind CSS for styling
- Vitest for unit tests
- agent-browser CLI for E2E testing

## Development Workflow

### Python Virtual Environment
The server virtualenv is in `server/.venv`. **You MUST activate it when opening a new terminal:**
```bash
cd server
source .venv/bin/activate
```

### Test-Driven Development (TDD)
This project **strictly follows TDD**. Follow the 12-step cycle below:

```
1. SELECT     → Pick next unchecked TODO item
2. UNDERSTAND → Read design doc section
3. WRITE TESTS → Create failing tests (RED)
4. RUN TESTS  → Verify they fail correctly
5. IMPLEMENT  → Minimum code to pass
6. RUN TESTS  → Achieve GREEN
7. ITERATE    → Repeat 5-6 until all pass
8. REFACTOR   → Clean code (tests stay green)
9. VALIDATE   → Run full test suite
10. UPDATE    → Mark TODO checkboxes
11. COMMIT    → Git commit with message
12. REPEAT    → Back to step 1
```

**Core TDD Rules:**
1. **Never write implementation before tests**
2. Tests must fail (RED) before making them pass (GREEN)
3. Refactor only when tests are green
4. All tests must pass before committing
5. Code coverage ≥80%

**Quality Gates Before Commit:**
- All tests pass
- Code coverage ≥80%
- No linting errors
- Type checking passes
- Keep functions <50 lines

## Claude Code Skills & Automation

### Skills (Invokable Workflows)

This project includes custom Claude Code skills for common workflows. See `skills/README.md` for details.

**Available skills:**
- `/start-servers` - Start backend and frontend with health checks
- `/test-ui` - Run agent-browser UI testing workflow
- `/db-inspect` - Quick database health check and statistics

**Installation:**
```bash
# Install globally for use in all Claude Code sessions
mkdir -p ~/.config/claude/skills
cp skills/*.md ~/.config/claude/skills/
```

**Usage:**
Just type the skill name in Claude Code:
```
/start-servers
```

### Hooks (Automatic Validations)

Hooks provide automatic safety checks. See `HOOKS_SETUP.md` for complete configuration.

**Recommended hooks:**
- `before_bash` - Warn when running Python without venv activated
- `after_edit` - Remind to run tests after editing code files

**Quick setup:**
Edit `~/.config/claude/settings.json` and add hooks from `HOOKS_SETUP.md`.

## Common Commands

### Server (Python/FastAPI)

**Activate virtualenv:**
```bash
cd server
source .venv/bin/activate  # Required for every new terminal
```

**Run server:**
```bash
cd server
source .venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Run all tests:**
```bash
cd server
source .venv/bin/activate
pytest
```

**Run specific test file:**
```bash
pytest tests/unit/test_face_detector.py -v
```

**Run with coverage:**
```bash
pytest --cov=app --cov-report=html
pytest --cov=app --cov-report=term  # Terminal output
```

**Code formatting:**
```bash
black app/ tests/
```

**Type checking:**
```bash
mypy app/
```

**Linting:**
```bash
flake8 app/ tests/
```

**Install dependencies:**
```bash
pip install -r requirements.txt
pip install -e ".[dev]"  # Development dependencies
```

### Web UI (SvelteKit)

**Run dev server:**
```bash
cd web-ui
npm run dev
# or with auto-open
npm run dev -- --open
```

**Run tests:**
```bash
cd web-ui
npm test              # Run once
npm run test:watch    # Watch mode
npm run test:coverage # With coverage
```

**Build for production:**
```bash
npm run build
npm run preview  # Preview production build
```

**Type checking:**
```bash
npm run check
npm run check:watch  # Watch mode
```

**Install dependencies:**
```bash
npm install  # or pnpm install or yarn
```

### agent-browser (E2E Testing)

The web UI uses `agent-browser` for automated browser testing.

**Basic workflow:**
```bash
agent-browser open http://localhost:5173
agent-browser snapshot -i              # Get interactive elements
agent-browser click @e1                # Click using refs
agent-browser screenshot page.png      # Capture screenshot
agent-browser console                  # Check for errors
agent-browser close
```

**Essential Commands:**
```bash
# Navigation
agent-browser open <url>
agent-browser back/forward/reload

# Interaction (always use refs from snapshot)
agent-browser click @e1
agent-browser fill @e2 "text"
agent-browser press Enter
agent-browser hover @e3

# Information
agent-browser snapshot -i -c           # Interactive + compact
agent-browser get text @e1
agent-browser get url
agent-browser is visible @e1

# Debugging
agent-browser screenshot --full        # Full page screenshot
agent-browser console                  # Console logs
agent-browser errors                   # JS errors
agent-browser --headed open <url>      # Show browser window
```

**Best Practices:**
- Always use refs (`@e1`, `@e2`) instead of CSS selectors
- Run `snapshot -i` first to get interactive elements
- Use `--json` flag for machine-readable output
- Check console/errors after each interaction
- Use `--headed` mode for debugging visual issues

## Server Management

### Starting Services

**Start everything (recommended):**
```bash
./start-project.sh
```
This starts both backend (port 8000) and web UI (port 5173), logging to `log/` directory.

**Start individually:**
```bash
# Backend only
cd server && ./start-backend.sh

# Web UI only
cd web-ui && ./start-frontend.sh
```

### Accessing Services
- **Web UI**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs (Swagger)
- **API Docs**: http://localhost:8000/redoc (ReDoc)

### Stopping Services
```bash
# Stop backend
fuser -k 8000/tcp

# Stop web UI
fuser -k 5173/tcp

# Stop everything
fuser -k 8000/tcp 5173/tcp
```

### View Logs
```bash
# Backend logs
tail -f log/server.log

# Web UI logs
tail -f log/web-ui.log

# Both simultaneously
tail -f log/*.log
```

### Health Checks
```bash
# Check backend
curl http://localhost:8000/health

# Check web UI
curl http://localhost:5173
```

## Database Access

### Production Database
- **Path**: `server/data/prison_rollcall.db`
- **Type**: SQLite 3

### Quick Access Methods

**SQLite CLI:**
```bash
cd server
sqlite3 data/prison_rollcall.db
# Commands: .tables, .schema tablename, SELECT..., .quit
```

**Python (with venv):**
```bash
cd server && source .venv/bin/activate
python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')
conn.row_factory = sqlite3.Row
cursor = conn.execute('SELECT COUNT(*) FROM inmates')
print(cursor.fetchone()[0])
"
```

**Quick Stats:**
```bash
cd server && source .venv/bin/activate && python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')
print('=== Database Stats ===')
for table in ['inmates', 'locations', 'schedule_entries', 'roll_calls', 'verifications']:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'{table}: {count}')
    except: pass
"
```

### Key Tables
- `inmates` - Prisoner records with home_cell_id
- `locations` - Location hierarchy (houseblocks, wings, landings, cells)
- `location_connections` - Walking distances between locations
- `schedule_entries` - Prisoner schedules/regimes
- `roll_calls` - Roll call records
- `verifications` - Individual verification records
- `embeddings` - Face embeddings for enrolled prisoners

### Location Types
`houseblock`, `wing`, `landing`, `cell`, `healthcare`, `education`, `workshop`, `gym`

## Worktree Best Practices

When working in a worktree (not main repo):

### Identifying Context
```bash
# Check current worktree
pwd  # /home/george_cairns/code/rightplace-worktrees/feature-name

# List all worktrees
git worktree list

# Show current branch
git branch --show-current
```

### Using Shared Resources
```bash
# Use shared venv (don't create a new one)
source /home/george_cairns/code/rightplace/server/.venv/bin/activate

# Install web UI dependencies if needed
cd web-ui && npm install
```

### Workflow
1. Create worktree: `./scripts/worktree-new.sh feature-name`
2. Develop and commit freely (isolated branch)
3. Push: `git push -u origin feature-name`
4. Create PR and merge to main
5. Cleanup: `./scripts/worktree-remove.sh feature-name`

### Important Notes
- Database is shared by default (unless explicitly copied)
- Keep worktrees short-lived (days, not weeks)
- Sync with main regularly: `git fetch origin && git rebase origin/main`
- One task per worktree
- Remove worktrees after merging

## Key Design Documents

- `prison-rollcall-design-document-v3.md`: Overall system design and MVP architecture
- `docs/web-ui-overview.md`: Web UI architecture and workflows
- `docs/web-ui-screens.md`: Screen specifications for web UI
- `docs/rollcall-location-centric-design.md`: Location-centric roll call design
- `PROJECT_TODO.md`: Development roadmap and task tracking

## Critical Architecture Patterns

### Face Recognition Pipeline

1. **Face Detection**: `app/ml/face_detector.py` wraps DeepFace detector
2. **Embedding Extraction**: DeepFace Facenet512 model extracts 512-dim embeddings
3. **Face Matching**: Cosine similarity matching in `app/services/verification_service.py`
4. **Storage**: Embeddings stored in `embeddings` table, indexed by `inmate_id`

### Repository Layer Best Practices

All repositories follow this pattern:
- Accept `Session` in constructor (dependency injection)
- Raise specific exceptions (`InmateNotFoundError`, `LocationNotFoundError`, etc.)
- Return domain models (`Inmate`, `Location`, etc.), not raw DB rows
- Use type hints for all methods
- Include docstrings for public methods

Example:
```python
class InmateRepository:
    def __init__(self, session: Session):
        self.session = session

    def get_by_id(self, inmate_id: int) -> Inmate:
        """Fetch inmate by ID."""
        row = self.session.execute(
            select(inmates).where(inmates.c.id == inmate_id)
        ).first()
        if not row:
            raise InmateNotFoundError(f"Inmate {inmate_id} not found")
        return Inmate.model_validate(dict(row._mapping))
```

### Service Layer Best Practices

Services contain business logic and orchestrate repositories:
- Accept repositories and config in constructor
- Implement single responsibility (VerificationService, RollCallService, etc.)
- Handle errors and return meaningful exceptions
- Do not access database directly (use repositories)

Example:
```python
class VerificationService:
    def __init__(
        self,
        inmate_repo: InmateRepository,
        embedding_repo: EmbeddingRepository,
        detector: FaceDetector,
        recognizer: FaceRecognizer,
    ):
        self.inmate_repo = inmate_repo
        self.embedding_repo = embedding_repo
        self.detector = detector
        self.recognizer = recognizer

    def verify_face(self, image_bytes: bytes, expected_inmate_id: int) -> VerificationResult:
        """Verify a face matches the expected inmate."""
        # Business logic here
        pass
```

### API Route Best Practices

Routes are thin adapters that:
- Use dependency injection for config, session, services
- Validate input with Pydantic models
- Return appropriate HTTP status codes
- Handle exceptions and map to HTTP errors
- Delegate business logic to services

Example:
```python
@router.post("/inmates", response_model=InmateResponse)
def create_inmate(
    inmate: InmateCreate,
    session: Session = Depends(get_db_session),
    settings: Settings = Depends(get_settings),
):
    """Create a new inmate."""
    repo = InmateRepository(session)
    # Delegate to service layer
    return repo.create(inmate)
```

## Database Schema

The database uses SQLite with SQLAlchemy Core (no ORM). Key tables:

- **inmates**: Inmate records (prisoner_number, full_name, dob, home_cell_id)
- **locations**: Physical locations (name, type, parent_id for hierarchy, connections JSON)
- **embeddings**: Face embeddings (inmate_id, embedding BLOB, model_name, enrollment_timestamp)
- **roll_calls**: Roll call sessions (status, created_by, started_at, completed_at, ordered_locations JSON)
- **verifications**: Verification attempts (roll_call_id, location_id, expected_inmate_id, detected_faces JSON)

**Important:**
- Always use repositories to access the database
- Never write raw SQL in routes or services
- Use parameterized queries to prevent SQL injection
- Wrap multi-table operations in transactions

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test individual functions/classes in isolation
- Mock external dependencies (DB, ML models, file I/O)
- Fast execution (<1 second per test)
- Follow Arrange-Act-Assert pattern

### Integration Tests (`tests/integration/`)
- Test API endpoints end-to-end
- Use real database (test DB fixture)
- Mock ML models (too slow for CI)
- Test repository + service + route integration

### Test Fixtures (`tests/fixtures/`)
- Diverse face images from LFW dataset (15 people, 36 images)
- Test database fixtures in `conftest.py`
- Shared test data in `fixtures/README.md`

### Test Naming Convention

**Python (pytest):**
```python
def test_<method>_<scenario>_<expected>():
    """Should <behavior> when <condition>"""
    # Arrange
    # Act
    # Assert
```

**TypeScript (Vitest):**
```typescript
describe('ComponentName', () => {
  it('should <behavior> when <condition>', () => {
    // Arrange, Act, Assert
  });
});
```

## Project TODO Tracking

`PROJECT_TODO.md` tracks all development tasks with 4 checkboxes per item:
- `[x] 📋 Design Complete` - Design/spec ready
- `[x] 🏗️ Built` - Implementation complete
- `[x] 🧪 Tests Created` - Tests written
- `[x] ✅ All Tests Pass` - All tests passing

**When working on tasks:**
1. Find the first unchecked TODO item
2. Read the design document section
3. Write tests first (RED)
4. Implement (GREEN)
5. Refactor (keep tests green)
6. Update all 4 checkboxes
7. Commit with descriptive message

## Git Workflow

**Commit message format:**
```
<type>(<scope>): <subject>

feat: New feature
fix: Bug fix
test: Adding tests
refactor: Code improvement
docs: Documentation
```

**Example:**
```bash
git add app/services/verification_service.py tests/unit/test_verification_service.py
git commit -m "feat(verification): add face matching service"
```

## Git Worktrees for Parallel Agent Development

Git worktrees enable multiple Claude Code instances to work on different features simultaneously without conflicts. See `docs/WORKTREE_GUIDE.md` for complete documentation.

### Directory Structure
```
/home/george_cairns/code/
├── rightplace/                    # Main worktree (main branch)
└── rightplace-worktrees/          # Container for feature worktrees
    ├── feature-auth/
    ├── bugfix-face-detection/
    └── ...
```

### Quick Commands

```bash
# Create new worktree for a feature
./scripts/worktree-new.sh feature-my-feature

# List all worktrees
./scripts/worktree-list.sh

# Open worktree in VSCode (start new Claude Code session)
code /home/george_cairns/code/rightplace-worktrees/feature-my-feature

# Remove worktree after merging
./scripts/worktree-remove.sh feature-my-feature
```

### Naming Conventions

| Prefix | Use Case |
|--------|----------|
| `feature-` | New features |
| `bugfix-` | Bug fixes |
| `refactor-` | Code improvements |
| `experiment-` | Experimental work |

### Workflow for Multi-Agent Development

1. **Create a worktree** for each independent task
2. **Open separate VSCode windows** for each worktree
3. **Start Claude Code** in each window - they work in isolation
4. **Merge branches** when tasks complete
5. **Remove worktrees** to clean up

## Security Considerations

- **No internet connectivity** - closed local network only
- **AES-256 encryption** at rest for sensitive data
- **API key authentication** for all endpoints (planned)
- **Face embeddings are one-way** - cannot reconstruct original face
- **No external APIs** - all ML runs locally
- **No sensitive data in git** - use .gitignore for credentials

## Common Pitfalls

1. **Forgetting to activate virtualenv** - Always `source .venv/bin/activate` in new terminals
2. **Writing implementation before tests** - Follow TDD strictly
3. **Putting business logic in routes** - Use service layer
4. **Raw SQL in routes** - Use repositories
5. **Skipping test coverage** - Maintain ≥80% coverage
6. **Not reading design docs** - Always check design before implementing

## API Documentation

Once the server is running, access interactive API docs:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Performance Notes

- **ML inference is CPU-bound** - Server requires 16GB RAM minimum
- **GPU acceleration** - Optional NVIDIA RTX 3060+ for faster inference
- **Image compression** - Mobile clients should compress images before upload
- **Embedding cache** - Embeddings are cached in database for fast matching
- **Connection pooling** - SQLAlchemy handles DB connection pooling
