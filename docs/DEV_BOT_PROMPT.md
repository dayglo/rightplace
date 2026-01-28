# Prison Roll Call - Web UI Development Prompt

## 🚀 Quick Start for New Dev Bot Sessions

Copy and paste this prompt when starting a new development session:

---

```
I am an autonomous development agent working on the Prison Roll Call Web UI.

## PROJECT CONTEXT
This is a SvelteKit + Tailwind CSS web application that provides a demo interface for a prison roll call system with face recognition. The backend (FastAPI) is fully functional.

## ESSENTIAL FILES TO READ FIRST
1. `PROJECT_TODO.md` - Find the first unchecked item in "WEB UI COMPONENTS" section
2. `docs/web-ui-overview.md` - Architecture and workflows
3. `docs/web-ui-screens.md` - Screen specifications and layouts
4. `docs/web-ui-iteration-loop.md` - TDD workflow with agent-browser testing

## MY WORKFLOW (12-Step TDD Cycle)
1. SELECT TASK → Pick next unchecked TODO item from PROJECT_TODO.md
2. UNDERSTAND → Read relevant design doc section
3. WRITE TESTS → Create Vitest unit tests + agent-browser verification script
4. RUN TESTS → Verify tests fail (RED)
5. IMPLEMENT → Build SvelteKit component/page
6. RUN TESTS → Run Vitest tests
7. ITERATE → Debug until passing (GREEN)
8. BROWSER VERIFY → Run agent-browser automated checks
9. REFACTOR → Clean code while tests stay green
10. FINAL CHECK → Full test suite + screenshots
11. UPDATE TODO → Mark checkboxes complete in PROJECT_TODO.md
12. COMMIT → Git commit with clear message

## RULES
- Always write tests BEFORE implementation (TDD)
- Use Vitest for unit tests, agent-browser for E2E verification
- Follow Tailwind CSS styling patterns from docs/web-ui-screens.md
- Backend runs at http://localhost:8000/api/v1
- Web UI runs at http://localhost:5173
- Never skip tests or mark TODO items complete without passing tests
- Commit only when all tests pass
- Run full test suite before marking TODO complete

## TESTING COMMANDS
- Vitest: `npm test`
- Vitest (watch): `npm test -- --watch`
- Vitest (coverage): `npm test -- --coverage`
- Browser: `agent-browser open http://localhost:5173`
- Snapshot: `agent-browser snapshot -i`
- Screenshot: `agent-browser screenshot page.png`
- Console errors: `agent-browser errors`

## QUALITY GATES
- ✅ All Vitest tests pass
- ✅ All agent-browser tests pass
- ✅ Code coverage ≥80%
- ✅ No console errors
- ✅ Screenshots captured
- ✅ Responsive design verified

## CURRENT TASK
Read PROJECT_TODO.md and find the first unchecked item in the "WEB UI COMPONENTS" section. Begin with Step 1: SELECT TASK from the iteration loop.

Let's start building!
```

---

## Usage Instructions

1. **Copy the prompt above** when starting a new dev bot session
2. The bot will automatically:
   - Read PROJECT_TODO.md
   - Find the next unchecked item
   - Follow the TDD iteration loop
   - Use agent-browser for UI verification
   - Update TODO checkboxes as work completes
3. **Monitor progress** by checking PROJECT_TODO.md checkboxes

## Key Design Documents

- **web-ui-overview.md** - Architecture, technology stack, workflows
- **web-ui-screens.md** - Detailed screen specifications with layouts
- **web-ui-iteration-loop.md** - Complete TDD workflow guide

## Backend API

The FastAPI backend is fully functional and running at `http://localhost:8000/api/v1`

Key endpoints:
- `GET /inmates` - List prisoners
- `POST /inmates` - Create prisoner
- `POST /enrollment/{inmate_id}` - Enroll face
- `POST /verify/quick` - Verify face at location
- `GET /locations` - List locations
- `POST /locations` - Create location
- `GET /rollcalls` - List roll calls
- `POST /rollcalls` - Create roll call
- `POST /rollcalls/{id}/start` - Start roll call
- `POST /rollcalls/{id}/verification` - Record verification

## Development Environment

- **Node.js**: v20+
- **Package Manager**: npm
- **Framework**: SvelteKit
- **Styling**: Tailwind CSS
- **Testing**: Vitest + agent-browser
- **Backend**: FastAPI (Python 3.11+)

## Success Criteria

Each TODO item is complete when:
- [x] 📋 Design Complete
- [x] 🏗️ Built
- [x] 🧪 Tests Created
- [x] ✅ All Tests Pass

---

*Last Updated: January 2026*
