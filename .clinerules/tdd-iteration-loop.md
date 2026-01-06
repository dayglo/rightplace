# Test-Driven Development Iteration Loop

## The 12-Step TDD Cycle

When implementing TODO items from PROJECT_TODO.md, follow this cycle:

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

## Core Rules

### Tests First, Always
- **Never write implementation before tests**
- Tests define "done" - they are the specification
- See tests fail (RED) before making them pass (GREEN)
- Refactor only when tests are green

### TODO Tracking
When working with PROJECT_TODO.md, update all 4 checkboxes:
- `[x] 📋 Design Complete` - Design/spec ready
- `[x] 🏗️ Built` - Implementation complete
- `[x] 🧪 Tests Created` - Tests written
- `[x] ✅ All Tests Pass` - All tests passing

### Test Commands

**Python/FastAPI**:
```bash
pytest tests/unit/test_feature.py -v           # Single test
pytest --cov=app --cov-report=term            # With coverage
```

**React Native/TypeScript**:
```bash
npm test -- __tests__/unit/feature.test.ts    # Single test
npm test -- --coverage                         # With coverage
```

### Quality Gates
- ✅ All tests pass before commit
- ✅ Code coverage ≥80%
- ✅ No linting errors
- ✅ Type checking passes
- ✅ Keep functions <50 lines

### Test Structure

**Python (pytest)**:
```python
def test_<method>_<scenario>_<expected>():
    """Should <behavior> when <condition>"""
    # Arrange - Set up test data
    # Act - Execute the code
    # Assert - Verify results
```

**TypeScript (Jest)**:
```typescript
describe('ComponentName', () => {
  it('should <behavior> when <condition>', () => {
    // Arrange, Act, Assert
  });
});
```

### Commit Messages
```
<type>(<scope>): <subject>

feat: New feature
fix: Bug fix
test: Adding tests
refactor: Code improvement
```

## TDD Principles

### YAGNI (You Aren't Gonna Need It)
Only implement what tests require. No speculative features.

### KISS (Keep It Simple, Stupid)
Simplest solution that makes tests pass. Complexity is refactored later.

### Red-Green-Refactor
🔴 **RED** → Write failing test
🟢 **GREEN** → Make it pass quickly
🔵 **REFACTOR** → Clean up code

## When Working on a Task

1. **Find the TODO**: Open PROJECT_TODO.md, find first incomplete item
2. **Read the spec**: Check prison-rollcall-design-document-v3.md for requirements
3. **Write tests first**: Create comprehensive test cases
4. **Watch them fail**: Verify tests fail for the right reasons
5. **Implement**: Write minimal code to pass tests
6. **Iterate**: Debug and fix until all tests pass
7. **Refactor**: Improve code while keeping tests green
8. **Validate**: Run full test suite
9. **Update TODO**: Mark checkboxes complete
10. **Commit**: Clear message, push if needed
11. **Repeat**: Move to next TODO item

## Debugging When Stuck

1. Re-read the design document
2. Check similar existing code
3. Simplify the implementation
4. Run single test in isolation
5. Add print/console.log statements
6. Review test expectations

## Remember

- **Tests are not optional** - They define "done"
- **Commit only when green** - All tests must pass
- **Update TODO honestly** - Track real progress
- **Follow project patterns** - Check existing code
- **Document public APIs** - Docstrings and comments
- **Never skip validation** - Run full test suite before commit

## Success = All Checkboxes ✅

Every TODO item is complete when:
- Design is documented
- Tests are written
- Implementation works
- All tests pass
- Code is committed
