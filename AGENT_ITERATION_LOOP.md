# Agent Iteration Loop - Test-Driven Development Workflow

## Overview

This document defines the autonomous development workflow for AI agents working on the Prison Roll Call project. The workflow emphasizes test-driven development (TDD), independent operation, and continuous validation through automated tests.

---

## Core Principles

1. **Tests First, Always**: Write tests before implementation
2. **Red-Green-Refactor**: Follow the TDD cycle religiously
3. **Incremental Progress**: Complete one TODO item at a time
4. **Validation-Driven**: Let tests guide correctness
5. **Self-Sufficient**: Work independently without human intervention during the cycle
6. **Documentation**: Update TODO tracking after each completion

---

## The Iteration Loop

```
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  1. SELECT TASK        →  Pick next unchecked TODO item    │
│          ↓                                                  │
│  2. UNDERSTAND         →  Read design doc + specs          │
│          ↓                                                  │
│  3. WRITE TESTS        →  Create failing tests (RED)       │
│          ↓                                                  │
│  4. RUN TESTS          →  Verify tests fail as expected    │
│          ↓                                                  │
│  5. IMPLEMENT          →  Write minimum code to pass       │
│          ↓                                                  │
│  6. RUN TESTS          →  Run tests (GREEN)                │
│          ↓                                                  │
│  7. ITERATE            →  If failing, go to step 5         │
│          ↓                                                  │
│  8. REFACTOR           →  Improve code quality             │
│          ↓                                                  │
│  9. FINAL VALIDATION   →  Run full test suite              │
│          ↓                                                  │
│  10. UPDATE TODO       →  Mark checkboxes complete         │
│          ↓                                                  │
│  11. COMMIT            →  Git commit with clear message    │
│          ↓                                                  │
│  REPEAT ────────────────→  Go to step 1                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Detailed Workflow Steps

### Step 1: SELECT TASK

**Objective**: Choose the next TODO item to work on.

**Actions**:
1. Open `PROJECT_TODO.md`
2. Find the first unchecked item in sequence
3. Read all four checkboxes for that item:
   - [ ] 📋 Design Complete
   - [ ] 🏗️ Built
   - [ ] 🧪 Tests Created
   - [ ] ✅ All Tests Pass
4. Determine which checkbox to work on next

**Decision Tree**:
- If 📋 not checked → Work on design/spec
- If 📋 checked but 🧪 not checked → Work on tests
- If 🧪 checked but 🏗️ not checked → Work on implementation
- If 🏗️ checked but ✅ not checked → Debug and fix tests

**Output**: Clear understanding of what to build next

---

### Step 2: UNDERSTAND

**Objective**: Gather all context needed to implement correctly.

**Actions**:
1. Read the relevant section in `prison-rollcall-design-document-v3.md`
2. Identify:
   - **Inputs**: What data/parameters are needed?
   - **Outputs**: What should be returned/produced?
   - **Behavior**: What are the expected behaviors?
   - **Edge Cases**: What error conditions exist?
   - **Dependencies**: What other components are needed?
3. Read existing related code to understand patterns
4. Review API contracts, data models, or schemas

**Checklist**:
- [ ] I understand the expected inputs
- [ ] I understand the expected outputs
- [ ] I understand the success criteria
- [ ] I understand the error conditions
- [ ] I understand the dependencies
- [ ] I know which files to create/modify

**Output**: Mental model of what to build

---

### Step 3: WRITE TESTS

**Objective**: Create comprehensive tests that define correct behavior.

**Test-First Principle**: Tests are specifications. They define "done."

#### For SERVER (Python/Pytest):

**Test Structure**:
```python
# tests/unit/test_<module>.py or tests/integration/test_<feature>.py

import pytest
from app.services.your_service import YourService

class TestYourFeature:
    """Test suite for [feature name]"""
    
    def test_happy_path(self, fixture1, fixture2):
        """Should succeed when given valid inputs"""
        # Arrange
        service = YourService()
        valid_input = fixture1
        
        # Act
        result = service.do_something(valid_input)
        
        # Assert
        assert result.success is True
        assert result.data == expected_value
    
    def test_validation_error(self):
        """Should raise ValidationError when input invalid"""
        # Arrange
        service = YourService()
        invalid_input = None
        
        # Act & Assert
        with pytest.raises(ValidationError):
            service.do_something(invalid_input)
    
    def test_edge_case_empty(self):
        """Should handle empty input gracefully"""
        # Arrange
        service = YourService()
        
        # Act
        result = service.do_something([])
        
        # Assert
        assert result.success is True
        assert result.data == []
```

**Test Categories**:
1. **Happy Path**: Valid inputs → expected outputs
2. **Validation**: Invalid inputs → proper errors
3. **Edge Cases**: Empty, null, boundary values
4. **Integration**: Component interactions
5. **Error Handling**: Network failures, timeouts, etc.

**Coverage Requirements**:
- Minimum 80% line coverage
- 100% of public API surface
- All error paths tested

#### For MOBILE (Jest/React Native):

**Test Structure**:
```typescript
// __tests__/unit/yourFeature.test.ts

import { renderHook, act } from '@testing-library/react-hooks';
import { render, fireEvent, waitFor } from '@testing-library/react-native';
import { useYourHook } from '../src/hooks/useYourHook';
import { YourComponent } from '../src/components/YourComponent';

describe('useYourHook', () => {
  it('should return initial state', () => {
    const { result } = renderHook(() => useYourHook());
    
    expect(result.current.data).toBeNull();
    expect(result.current.loading).toBe(false);
  });
  
  it('should load data successfully', async () => {
    const mockData = { id: '123', name: 'Test' };
    mockApi.getData.mockResolvedValue(mockData);
    
    const { result } = renderHook(() => useYourHook());
    
    await act(async () => {
      await result.current.loadData();
    });
    
    expect(result.current.data).toEqual(mockData);
    expect(result.current.loading).toBe(false);
  });
  
  it('should handle errors', async () => {
    mockApi.getData.mockRejectedValue(new Error('Network error'));
    
    const { result } = renderHook(() => useYourHook());
    
    await act(async () => {
      await result.current.loadData();
    });
    
    expect(result.current.error).toBe('Network error');
    expect(result.current.data).toBeNull();
  });
});

describe('YourComponent', () => {
  it('should render correctly', () => {
    const { getByText } = render(<YourComponent title="Test" />);
    
    expect(getByText('Test')).toBeTruthy();
  });
  
  it('should handle button press', () => {
    const onPress = jest.fn();
    const { getByText } = render(
      <YourComponent title="Test" onPress={onPress} />
    );
    
    fireEvent.press(getByText('Test'));
    
    expect(onPress).toHaveBeenCalledTimes(1);
  });
});
```

**Actions**:
1. Create test file in appropriate directory
2. Write test cases covering all scenarios
3. Include fixtures/mocks as needed
4. Use descriptive test names
5. Follow AAA pattern (Arrange, Act, Assert)

**Output**: Complete test file ready to run

---

### Step 4: RUN TESTS (RED)

**Objective**: Verify tests fail for the right reasons.

**Commands**:

**Server**:
```bash
# Run specific test file
pytest tests/unit/test_your_feature.py -v

# Run with coverage
pytest tests/unit/test_your_feature.py --cov=app.services.your_service --cov-report=term
```

**Mobile**:
```bash
# Run specific test file
npm test -- __tests__/unit/yourFeature.test.ts

# Run with coverage
npm test -- --coverage --testPathPattern=yourFeature
```

**Expected Outcome**: All tests should FAIL with clear error messages:
- `ModuleNotFoundError` (Python) or `Cannot find module` (TS) → Good! Module doesn't exist yet
- `AttributeError` or `TypeError` → Good! Function doesn't exist yet
- Assertion failures → Good! Function exists but returns wrong value

**Red Flags** (Bad Failures):
- Syntax errors in test code → Fix tests
- Import errors for test dependencies → Fix test setup
- Tests passing without implementation → Tests are wrong!

**Actions**:
1. Run test command
2. Read failure messages carefully
3. Verify failures match expectations
4. If tests fail incorrectly, fix tests and repeat

**Output**: Confidence that tests correctly specify behavior

---

### Step 5: IMPLEMENT

**Objective**: Write the minimum code to make tests pass.

**Principles**:
- **YAGNI**: You Aren't Gonna Need It - only implement what tests require
- **KISS**: Keep It Simple, Stupid - simplest solution that works
- **DRY**: Don't Repeat Yourself - refactor duplication later

**Implementation Patterns**:

#### Server (Python/FastAPI):

**Repository Pattern**:
```python
# app/db/repositories/inmate_repo.py

from typing import Optional, List
from datetime import datetime
import sqlite3
from app.models.inmate import Inmate, InmateCreate

class InmateRepository:
    """Repository for inmate data operations"""
    
    def __init__(self, db: sqlite3.Connection):
        self.db = db
    
    def create(self, inmate: InmateCreate) -> Inmate:
        """Create new inmate record"""
        cursor = self.db.cursor()
        now = datetime.utcnow().isoformat()
        inmate_id = str(uuid.uuid4())
        
        cursor.execute("""
            INSERT INTO inmates 
            (id, inmate_number, first_name, last_name, date_of_birth, 
             cell_block, cell_number, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            inmate_id, inmate.inmate_number, inmate.first_name,
            inmate.last_name, inmate.date_of_birth, inmate.cell_block,
            inmate.cell_number, now, now
        ))
        self.db.commit()
        
        return self.get_by_id(inmate_id)
    
    def get_by_id(self, inmate_id: str) -> Optional[Inmate]:
        """Get inmate by ID"""
        cursor = self.db.cursor()
        row = cursor.execute(
            "SELECT * FROM inmates WHERE id = ?", (inmate_id,)
        ).fetchone()
        
        if not row:
            return None
        
        return self._row_to_inmate(row)
    
    def _row_to_inmate(self, row) -> Inmate:
        """Convert database row to Inmate model"""
        return Inmate(
            id=row[0],
            inmate_number=row[1],
            first_name=row[2],
            # ... map all fields
        )
```

**Service Pattern**:
```python
# app/services/inmate_service.py

from app.db.repositories.inmate_repo import InmateRepository
from app.models.inmate import Inmate, InmateCreate

class InmateService:
    """Business logic for inmate operations"""
    
    def __init__(self, repo: InmateRepository):
        self.repo = repo
    
    def create_inmate(self, inmate_data: InmateCreate) -> Inmate:
        """Create new inmate with validation"""
        # Business logic here
        if not inmate_data.inmate_number:
            raise ValueError("Inmate number required")
        
        return self.repo.create(inmate_data)
```

**API Endpoint Pattern**:
```python
# app/api/routes/inmates.py

from fastapi import APIRouter, Depends, HTTPException
from app.models.inmate import Inmate, InmateCreate
from app.services.inmate_service import InmateService
from app.dependencies import get_inmate_service

router = APIRouter(prefix="/inmates", tags=["inmates"])

@router.post("/", response_model=Inmate, status_code=201)
async def create_inmate(
    inmate: InmateCreate,
    service: InmateService = Depends(get_inmate_service)
):
    """Create new inmate"""
    try:
        return service.create_inmate(inmate)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

#### Mobile (React Native/TypeScript):

**Hook Pattern**:
```typescript
// src/hooks/useInmates.ts

import { useState, useEffect } from 'react';
import { inmateApi } from '../services/api';
import { Inmate } from '../types';

export function useInmates() {
  const [inmates, setInmates] = useState<Inmate[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadInmates = async () => {
    setLoading(true);
    setError(null);
    
    try {
      const data = await inmateApi.getAll();
      setInmates(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadInmates();
  }, []);

  return { inmates, loading, error, reload: loadInmates };
}
```

**Component Pattern**:
```typescript
// src/components/InmateCard.tsx

import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { Inmate } from '../types';

interface InmateCardProps {
  inmate: Inmate;
  onPress?: () => void;
}

export function InmateCard({ inmate, onPress }: InmateCardProps) {
  return (
    <View style={styles.card} onPress={onPress}>
      <Text style={styles.name}>
        {inmate.firstName} {inmate.lastName}
      </Text>
      <Text style={styles.number}>{inmate.inmateNumber}</Text>
      <Text style={styles.location}>
        Block {inmate.cellBlock}, Cell {inmate.cellNumber}
      </Text>
    </View>
  );
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    backgroundColor: '#fff',
    borderRadius: 8,
    marginVertical: 8,
  },
  name: {
    fontSize: 18,
    fontWeight: 'bold',
  },
  number: {
    fontSize: 14,
    color: '#666',
  },
  location: {
    fontSize: 14,
    color: '#999',
  },
});
```

**Actions**:
1. Create implementation file(s)
2. Write minimal code to pass first test
3. Don't add features not required by tests
4. Follow project patterns and conventions
5. Add type hints (Python) or types (TypeScript)
6. Include docstrings/comments for public APIs

**Output**: Working implementation ready to test

---

### Step 6: RUN TESTS (GREEN)

**Objective**: Verify all tests pass.

**Commands**: Same as Step 4

**Expected Outcome**: All tests PASS with green checkmarks

**If Tests Fail**:
- Read failure message carefully
- Identify which assertion failed
- Debug the implementation
- Go back to Step 5

**Actions**:
1. Run test command
2. Verify all tests pass
3. Check coverage report
4. If coverage <80%, add more tests

**Output**: Green test suite with good coverage

---

### Step 7: ITERATE

**Objective**: Continue until all tests pass.

**Loop**: Repeat Steps 5-6 until:
- All test cases pass
- No test failures
- Coverage targets met
- No obvious bugs

**Debugging Strategies**:
1. **Print debugging**: Add print/console.log statements
2. **Debugger**: Use pdb (Python) or debugger (VS Code)
3. **Test isolation**: Run single test to isolate issue
4. **Read stack traces**: Follow error messages carefully
5. **Check assumptions**: Verify test expectations are correct

**Common Issues**:
- **Off-by-one errors**: Check loop conditions
- **Type mismatches**: Verify data types
- **Null/undefined**: Add null checks
- **Async issues**: Ensure proper await/async usage
- **Mock problems**: Verify mocks are set up correctly

**When Stuck**:
1. Re-read the design document
2. Check similar existing code
3. Simplify the implementation
4. Break down into smaller steps
5. Review test expectations

**Output**: Working, tested implementation

---

### Step 8: REFACTOR

**Objective**: Improve code quality without changing behavior.

**Refactoring Checklist**:
- [ ] Remove duplication (DRY)
- [ ] Extract complex logic into functions
- [ ] Use meaningful variable names
- [ ] Follow project conventions
- [ ] Add helpful comments
- [ ] Simplify complex conditionals
- [ ] Break up long functions (<50 lines)
- [ ] Improve type hints/types
- [ ] Remove dead code
- [ ] Optimize obvious inefficiencies

**Rules**:
- **Tests must still pass after each change**
- **Never change behavior during refactoring**
- **Commit after each refactoring if tests pass**

**Red Flags**:
- Function >50 lines → Extract smaller functions
- Duplication → Extract common logic
- Magic numbers → Use named constants
- Complex conditionals → Extract predicate functions
- Deep nesting → Early returns or extraction

**Example Refactoring**:

**Before**:
```python
def process_inmate(inmate_data):
    if inmate_data is not None:
        if 'inmate_number' in inmate_data:
            if len(inmate_data['inmate_number']) > 0:
                return create_inmate(inmate_data)
    return None
```

**After**:
```python
def process_inmate(inmate_data: dict) -> Optional[Inmate]:
    """Process inmate data and create record if valid"""
    if not inmate_data:
        return None
    
    inmate_number = inmate_data.get('inmate_number', '')
    if not inmate_number:
        return None
    
    return create_inmate(inmate_data)
```

**Actions**:
1. Run tests before refactoring
2. Make one small refactoring
3. Run tests after refactoring
4. If tests pass, commit
5. Repeat until code is clean

**Output**: Clean, maintainable code with passing tests

---

### Step 9: FINAL VALIDATION

**Objective**: Ensure nothing broke elsewhere.

**Commands**:

**Server**:
```bash
# Run ALL tests
pytest

# Run with coverage
pytest --cov=app --cov-report=term --cov-report=html

# Check coverage report
open htmlcov/index.html
```

**Mobile**:
```bash
# Run ALL tests
npm test

# Run with coverage
npm test -- --coverage

# Run type checking
npm run typecheck  # or npx tsc --noEmit
```

**Validation Checklist**:
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Coverage meets minimum (80%)
- [ ] No linting errors
- [ ] Type checking passes (TypeScript/mypy)
- [ ] No obvious performance issues
- [ ] Related components still work

**If Failures**:
- Fix broken tests
- Update tests if requirements changed
- Ensure your changes didn't break others

**Actions**:
1. Run full test suite
2. Run linter/formatter
3. Run type checker
4. Review coverage report
5. Fix any issues found

**Output**: Confidence that everything works

---

### Step 10: UPDATE TODO

**Objective**: Mark progress in tracking document.

**Actions**:
1. Open `PROJECT_TODO.md`
2. Find the item you just completed
3. Check off the appropriate checkbox:
   - `[x]` for completed
   - `[ ]` for not yet done
4. Update all four checkboxes as appropriate:
   - `[x] 📋 Design Complete` - if design is done
   - `[x] 🏗️ Built` - if implementation is done
   - `[x] 🧪 Tests Created` - if tests are written
   - `[x] ✅ All Tests Pass` - if all tests pass
5. Save the file

**Example Update**:

**Before**:
```markdown
#### 1.2 Configuration
- [ ] 📋 Config model designed (app/config.py)
- [ ] 🏗️ Config implementation built
- [ ] 🧪 Config validation tests created
- [ ] ✅ All tests pass
```

**After** (completed):
```markdown
#### 1.2 Configuration
- [x] 📋 Config model designed (app/config.py)
- [x] 🏗️ Config implementation built
- [x] 🧪 Config validation tests created
- [x] ✅ All tests pass
```

**Output**: Updated TODO with accurate progress

---

### Step 11: COMMIT

**Objective**: Save work with clear commit message.

**Commit Message Format**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `test`: Adding tests
- `refactor`: Code refactoring
- `docs`: Documentation
- `chore`: Maintenance

**Examples**:

```bash
git add .
git commit -m "feat(server): implement InmateRepository with CRUD operations

- Add InmateRepository class with create, read, update, delete methods
- Implement database connection handling
- Add comprehensive unit tests with 95% coverage
- All tests passing

Closes #TODO-1.5"
```

```bash
git add .
git commit -m "test(mobile): add useVerification hook tests

- Add happy path tests for verification flow
- Add error handling tests
- Add offline queue tests
- Mock API responses

All tests passing"
```

**Actions**:
1. Review changes: `git status` and `git diff`
2. Stage files: `git add <files>` or `git add .`
3. Write clear commit message
4. Commit: `git commit -m "message"`
5. Push if working on remote: `git push`

**Output**: Clean commit in version control

---

### Step 12: REPEAT

**Objective**: Continue the cycle.

**Actions**:
1. Return to Step 1
2. Select next TODO item
3. Repeat the entire loop

**Progress Tracking**:
- Check `PROJECT_TODO.md` regularly
- Celebrate completed sections
- Notice patterns and improve efficiency

---

## Autonomous Agent Prompt

> **Use this prompt when starting work on the Prison Roll Call project:**

```
I am an autonomous development agent working on the Prison Roll Call project.

TASK: Implement the next incomplete item from PROJECT_TODO.md

WORKFLOW:
1. Read PROJECT_TODO.md and find the first incomplete TODO item
2. Read the relevant section from prison-rollcall-design-document-v3.md
3. Write comprehensive tests first (TDD approach)
4. Run tests and verify they fail (RED)
5. Implement the minimum code to pass tests
6. Run tests and iterate until passing (GREEN)
7. Refactor code for quality while keeping tests green
8. Run full test suite for validation
9. Update PROJECT_TODO.md with checkmarks
10. Commit changes with clear message
11. Report completion and move to next item

RULES:
- Always write tests BEFORE implementation
- Never skip tests or mark TODO items complete without passing tests
- Run tests after every change
- Commit only when all tests pass
- Keep functions under 50 lines
- Follow project patterns and conventions
- Use type hints (Python) or TypeScript types
- Document public APIs
- Never modify prison-rollcall-design-document-v3.md (it's the spec)

SUCCESS CRITERIA:
- All tests passing (pytest or npm test)
- Code coverage ≥80%
- No linting errors
- TODO checkboxes updated
- Clean git commit made

CURRENT TODO SECTION: [Agent fills this in]

Let's begin with Step 1: SELECT TASK...
```

---

## Test-Driven Development (TDD) Cheat Sheet

### The TDD Mantra

```
🔴 RED → Write a failing test
🟢 GREEN → Make it pass quickly
🔵 REFACTOR → Clean up the code
```

### Why TDD?

1. **Specification**: Tests define what "done" means
2. **Safety Net**: Refactor with confidence
3. **Design**: Forces good architecture
4. **Documentation**: Tests show how to use code
5. **Debugging**: Find issues early
6. **Confidence**: Know when you're done

### TDD Best Practices

#### Write Good Tests

✅ **DO**:
- Test behavior, not implementation
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Test one thing per test
- Make tests independent
- Use fixtures for test data

❌ **DON'T**:
- Test private methods directly
- Make tests depend on each other
- Write tests that sometimes pass/fail
- Test framework code
- Over-mock (test the real thing when possible)

#### Test Naming Conventions

**Python (pytest)**:
```python
def test_<method>_<scenario>_<expected_result>():
    """Should <expected behavior> when <scenario>"""
```

Examples:
```python
def test_create_inmate_valid_data_returns_inmate():
    """Should return Inmate when given valid data"""

def test_verify_face_no_match_returns_no_match_response():
    """Should return no match response when confidence below threshold"""
```

**TypeScript (Jest)**:
```typescript
describe('ComponentName or functionName', () => {
  it('should <expected behavior> when <scenario>', () => {
    // test code
  });
});
```

Examples:
```typescript
describe('useVerification', () => {
  it('should queue verification when offline', async () => {
    // test
  });
  
  it('should return error when server unreachable', async () => {
    // test
  });
});
```

### Test Coverage Goals

| Type | Target | Minimum |
|------|--------|---------|
| Unit Tests | 90% | 80% |
| Integration Tests | 70% | 60% |
| E2E Tests | Critical paths | Happy paths |

### Test Organization

**Server Structure**:
```
tests/
├── unit/              # Fast, isolated tests
│   ├── test_services/
│   ├── test_repositories/
│   └── test_ml/
├── integration/       # Component interaction tests
│   ├── test_api/
│   └── test_workflows/
└── fixtures/          # Test data
    ├── images/
    └── data.py
```

**Mobile Structure**:
```
__tests__/
├── unit/              # Component and hook tests
│   ├── components/
│   ├── hooks/
│   └── utils/
├── integration/       # Feature flow tests
│   └── flows/
└── __mocks__/         # Mock modules
```

---

## Common Patterns & Examples

### Pattern 1: Repository Testing

```python
# tests/unit/test_inmate_repository.py

import pytest
from app.db.repositories.inmate_repo import InmateRepository
from app.models.inmate import InmateCreate

@pytest.fixture
def repo(test_db):
    """Create repository with test database"""
    return InmateRepository(test_db)

@pytest.fixture
def sample_inmate():
    """Sample inmate data for testing"""
    return InmateCreate(
        inmate_number="A12345",
        first_name="John",
        last_name="Doe",
        date_of_birth="1990-01-01",
        cell_block="A",
        cell_number="101"
    )

class TestInmateRepository:
    def test_create_valid_inmate_returns_inmate_with_id(self, repo, sample_inmate):
        """Should create inmate and return with generated ID"""
        result = repo.create(sample_inmate)
        
        assert result.id is not None
        assert result.inmate_number == "A12345"
        assert result.first_name == "John"
    
    def test_get_by_id_existing_returns_inmate(self, repo, sample_inmate):
        """Should return inmate when ID exists"""
        created = repo.create(sample_inmate)
        
        result = repo.get_by_id(created.id)
        
        assert result is not None
        assert result.id == created.id
    
    def test_get_by_id_nonexistent_returns_none(self, repo):
        """Should return None when ID doesn't exist"""
        result = repo.get_by_id("nonexistent-id")
        
        assert result is None
```

### Pattern 2: API Endpoint Testing

```python
# tests/integration/test_inmates_api.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def client():
    return TestClient(app)

class TestInmatesAPI:
    def test_create_inmate_valid_data_returns_201(self, client):
        """Should create inmate and return 201 when data valid"""
        payload = {
            "inmate_number": "A12345",
            "first_name": "John",
            "last_name": "Doe",
            "date_of_birth": "1990-01-01",
            "cell_block": "A",
            "cell_number": "101"
        }
        
        response = client.post("/api/v1/inmates", json=payload)
        
        assert response.status_code == 201
        data = response.json()
        assert data["inmate_number"] == "A12345"
        assert "id" in data
    
    def test_create_inmate_missing_field_returns_400(self, client):
        """Should return 400 when required field missing"""
        payload = {
            "first_name": "John"
            # Missing required fields
        }
        
        response = client.post("/api/v1/inmates", json=payload)
        
        assert response.status_code == 400
```

### Pattern 3: React Hook Testing

```typescript
// __tests__/hooks/useVerification.test.ts

import { renderHook, act } from '@testing-library/react-hooks';
import { useVerification } from '../../src/hooks/useVerification';
import * as api from '../../src/services/api';

jest.mock('../../src/services/api');

describe('useVerification', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });
  
  it('should initialize with default state', () => {
    const { result } = renderHook(() => useVerification());
    
    expect(result.current.result).toBeNull();
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });
  
  it('should verify successfully with valid image', async () => {
    const mockResult = {
      matched: true,
      inmateId: 'abc123',
      confidence: 0.89,
    };
    (api.verifyFace as jest.Mock).mockResolvedValue(mockResult);
    
    const { result } = renderHook(() => useVerification());
    
    await act(async () => {
      await result.current.verify('rollcall-1', 'loc-1', 'image-data');
    });
    
    expect(result.current.result).toEqual(mockResult);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
  });
  
  it('should handle errors gracefully', async () => {
    (api.verifyFace as jest.Mock).mockRejectedValue(
      new Error('Network error')
    );
    
    const { result } = renderHook(() => useVerification());
    
    await act(async () => {
      await result.current.verify('rollcall-1', 'loc-1', 'image-data');
    });
    
    expect(result.current.result).toBeNull();
    expect(result.current.error).toBe('Network error');
  });
});
```

---

## Troubleshooting Guide

### Common Issues

#### Issue: Tests won't run

**Python**:
```bash
# Check pytest installed
pip list | grep pytest

# Install if missing
pip install pytest pytest-cov

# Run from project root
cd server/
pytest
```

**TypeScript**:
```bash
# Check jest installed
npm list jest

# Install if missing
npm install --save-dev jest @testing-library/react-native

# Run tests
npm test
```

#### Issue: Import errors in tests

**Python**:
```python
# Add to conftest.py
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
```

**TypeScript**:
```json
// Update jest.config.js
module.exports = {
  preset: 'react-native',
  moduleDirectories: ['node_modules', 'src'],
};
```

#### Issue: Tests pass but shouldn't

**Check**:
1. Are you actually testing the right thing?
2. Are assertions correct?
3. Is test data realistic?
4. Are mocks set up correctly?

#### Issue: Tests fail intermittently

**Causes**:
- Async timing issues
- Test order dependency
- Shared state between tests
- External dependencies

**Solutions**:
- Use proper async/await
- Make tests independent
- Reset state in beforeEach
- Mock external calls

---

## Success Metrics

### Per TODO Item

- ✅ All 4 checkboxes marked
- ✅ Tests written before implementation
- ✅ All tests passing
- ✅ Code coverage ≥80%
- ✅ Clean git commit made

### Per Phase

- ✅ All items in phase complete
- ✅ Integration tests passing
- ✅ No regression in other phases
- ✅ Documentation updated

### Project Complete

- ✅ All TODO items checked
- ✅ All tests passing (unit + integration + E2E)
- ✅ Performance targets met
- ✅ Security review complete
- ✅ Ready for production

---

## Final Notes

### Remember

1. **Tests are not optional** - They define "done"
2. **Red before green** - Always see tests fail first
3. **Refactor fearlessly** - Tests protect you
4. **Commit often** - Small commits are better
5. **Read errors carefully** - They tell you what's wrong
6. **Ask for help** - When stuck, refer to design doc
7. **Celebrate progress** - Each checkbox is a win

### The Agent Mindset

- **Autonomous**: Work independently through the loop
- **Methodical**: Follow the steps religiously
- **Quality-focused**: Tests and clean code matter
- **Persistent**: Iterate until tests pass
- **Honest**: Update TODO accurately

### Getting Started

```bash
# 1. Read the TODO
cat PROJECT_TODO.md

# 2. Find first incomplete item
# 3. Read design doc section
# 4. Start the loop!
# 5. Write tests
# 6. Watch them fail (RED)
# 7. Make them pass (GREEN)
# 8. Clean up (REFACTOR)
# 9. Update TODO
# 10. Commit
# 11. REPEAT!
```

---

**Now go build something amazing, one test at a time!** 🚀
