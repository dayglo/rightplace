# Web UI Development - Auto-Loaded Context

## Quick Start Prompt

When working on the Web UI, use this prompt to get started:

```
I am working on the Prison Roll Call Web UI (SvelteKit + Tailwind CSS).

FIRST STEPS:
1. Read `docs/DEV_BOT_PROMPT.md` for the complete development prompt
2. Read `PROJECT_TODO.md` and find the first unchecked item in "WEB UI COMPONENTS"
3. Follow the 12-step TDD cycle from `docs/web-ui-iteration-loop.md`

ESSENTIAL DOCS:
- docs/DEV_BOT_PROMPT.md - Complete dev bot prompt
- docs/web-ui-overview.md - Architecture and workflows
- docs/web-ui-screens.md - Screen specifications
- docs/web-ui-iteration-loop.md - TDD workflow with agent-browser

WORKFLOW:
1. SELECT TASK from PROJECT_TODO.md
2. WRITE TESTS (Vitest + agent-browser)
3. IMPLEMENT (SvelteKit + Tailwind)
4. VERIFY (all tests pass)
5. UPDATE TODO checkboxes
6. COMMIT

Let's build!
```

## Key Points

- **Always TDD**: Write tests before implementation
- **Use agent-browser**: For automated UI verification
- **Follow designs**: All screens specified in docs/web-ui-screens.md
- **Quality gates**: 80% coverage, no console errors, all tests pass

## Backend API

Running at `http://localhost:8000/api/v1` - fully functional

## Web UI

Will run at `http://localhost:5173` (SvelteKit dev server)
