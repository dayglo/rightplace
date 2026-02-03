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
This project **strictly follows TDD**. See `.clinerules/tdd-iteration-loop.md` for the complete 12-step cycle.

**Core TDD Rules:**
1. **Never write implementation before tests**
2. Tests must fail (RED) before making them pass (GREEN)
3. Refactor only when tests are green
4. All tests must pass before committing
5. Code coverage ≥80%

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

The web UI uses `agent-browser` for automated browser testing. See `.clinerules/agent-browser-skill.md` for complete documentation.

**Basic workflow:**
```bash
agent-browser open http://localhost:5173
agent-browser snapshot -i              # Get interactive elements
agent-browser click @e1                # Click using refs
agent-browser screenshot page.png      # Capture screenshot
agent-browser console                  # Check for errors
agent-browser close
```

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
