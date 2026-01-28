# Web UI Development Iteration Loop

## Overview

This document defines the TDD workflow for building the SvelteKit web UI, incorporating **agent-browser** for automated UI verification. This iteration loop ensures quality, testability, and demo-readiness.

---

## The 12-Step TDD Cycle (Web UI Edition)

```
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  1. SELECT TASK     → Pick next unchecked TODO item    │
│          ↓                                              │
│  2. UNDERSTAND      → Read design doc section           │
│          ↓                                              │
│  3. WRITE TESTS     → Vitest unit tests + browser test │
│          ↓                                              │
│  4. RUN TESTS       → Verify tests fail (RED)           │
│          ↓                                              │
│  5. IMPLEMENT       → Build SvelteKit component/page    │
│          ↓                                              │
│  6. RUN TESTS       → Run Vitest tests                  │
│          ↓                                              │
│  7. ITERATE         → Debug until passing (GREEN)       │
│          ↓                                              │
│  8. BROWSER VERIFY  → agent-browser automated checks    │
│          ↓                                              │
│  9. REFACTOR        → Clean code (tests stay green)     │
│          ↓                                              │
│  10. FINAL CHECK    → Full test suite + screenshots     │
│          ↓                                              │
│  11. UPDATE TODO    → Mark checkboxes complete          │
│          ↓                                              │
│  12. COMMIT         → Git commit with clear message     │
│          ↓                                              │
│  REPEAT ─────────────→ Back to step 1                   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Step 1: SELECT TASK

**Objective:** Choose the next TODO item from PROJECT_TODO.md

**Actions:**
1. Open `PROJECT_TODO.md`
2. Find first unchecked item in Web UI section
3. Read all four checkboxes:
   - `[ ] 📋 Design Complete`
   - `[ ] 🏗️ Built`
   - `[ ] 🧪 Tests Created`
   - `[ ] ✅ All Tests Pass`

**Example:**
```markdown
#### Web UI 1.1: Home Page
- [x] 📋 Design Complete (see web-ui-screens.md)
- [ ] 🏗️ Built
- [ ] 🧪 Tests Created
- [ ] ✅ All Tests Pass
```

---

## Step 2: UNDERSTAND

**Objective:** Gather context for implementation

**Actions:**
1. Read relevant section in `docs/web-ui-screens.md`
2. Check `docs/web-ui-api-mapping.md` for endpoints
3. Review `docs/web-ui-components.md` for reusable components
4. Identify:
   - **Route:** What URL path?
   - **Components:** What UI elements needed?
   - **API calls:** What backend endpoints?
   - **User interactions:** What can user do?
   - **Success criteria:** What defines "done"?

---

## Step 3: WRITE TESTS

**Objective:** Create comprehensive tests before implementation

### A. Vitest Unit Tests

**For Components:**
```javascript
// src/lib/components/PrisonerCard.test.js
import { render } from '@testing-library/svelte';
import { describe, it, expect } from 'vitest';
import PrisonerCard from './PrisonerCard.svelte';

describe('PrisonerCard', () => {
  it('should display prisoner name and number', () => {
    const prisoner = {
      id: '123',
      first_name: 'John',
      last_name: 'Doe',
      inmate_number: 'A12345',
      is_enrolled: true
    };
    
    const { getByText } = render(PrisonerCard, { props: { prisoner } });
    
    expect(getByText('John Doe')).toBeTruthy();
    expect(getByText('#A12345')).toBeTruthy();
  });
  
  it('should show enrollment status icon', () => {
    const prisoner = { is_enrolled: true, /* ... */ };
    const { container } = render(PrisonerCard, { props: { prisoner } });
    
    const icon = container.querySelector('[data-testid="enrolled-icon"]');
    expect(icon).toBeTruthy();
  });
});
```

**For API Services:**
```javascript
// src/lib/services/api.test.js
import { describe, it, expect, vi, beforeEach } from 'vitest';
import { getPrisoners, createPrisoner } from './api';

describe('API Service', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
  });
  
  it('should fetch prisoners from API', async () => {
    const mockPrisoners = [{ id: '1', first_name: 'John' }];
    global.fetch.mockResolvedValue({
      ok: true,
      json: async () => mockPrisoners
    });
    
    const result = await getPrisoners();
    
    expect(global.fetch).toHaveBeenCalledWith('http://localhost:8000/api/v1/inmates');
    expect(result).toEqual(mockPrisoners);
  });
  
  it('should handle API errors', async () => {
    global.fetch.mockResolvedValue({
      ok: false,
      status: 500
    });
    
    await expect(getPrisoners()).rejects.toThrow();
  });
});
```

### B. agent-browser Test Script

**Create verification script:**
```bash
#!/bin/bash
# tests/browser/test_home_page.sh

# Test Home Page
echo "Testing Home Page..."

# 1. Navigate to home
agent-browser open http://localhost:5173
sleep 2

# 2. Take snapshot
agent-browser snapshot -i > tests/browser/snapshots/home_snapshot.txt

# 3. Verify key elements exist
agent-browser get text "h1" | grep -q "Prison Roll Call" || exit 1
echo "✓ Title found"

# 4. Check stats cards visible
agent-browser is visible "[data-testid='prisoners-stat']" || exit 1
agent-browser is visible "[data-testid='locations-stat']" || exit 1
echo "✓ Stat cards visible"

# 5. Take screenshot
agent-browser screenshot tests/browser/screenshots/home_page.png
echo "✓ Screenshot saved"

# 6. Check for console errors
agent-browser errors > tests/browser/logs/home_errors.txt
if [ -s tests/browser/logs/home_errors.txt ]; then
  echo "✗ Console errors found"
  cat tests/browser/logs/home_errors.txt
  exit 1
fi
echo "✓ No console errors"

# 7. Cleanup
agent-browser close

echo "✓ Home page tests passed"
```

---

## Step 4: RUN TESTS (RED)

**Objective:** Verify tests fail correctly

**Commands:**
```bash
# Run Vitest tests
npm test

# Run browser test
chmod +x tests/browser/test_home_page.sh
./tests/browser/test_home_page.sh
```

**Expected:** All tests should FAIL because implementation doesn't exist yet

---

## Step 5: IMPLEMENT

**Objective:** Build the feature

### SvelteKit Page Example

```svelte
<!-- src/routes/+page.svelte -->
<script>
  import { onMount } from 'svelte';
  import StatCard from '$lib/components/StatCard.svelte';
  import { getPrisoners, getLocations, getRollCalls } from '$lib/services/api';
  
  let prisonerCount = 0;
  let locationCount = 0;
  let recentRollCalls = [];
  let loading = true;
  
  onMount(async () => {
    try {
      const [prisoners, locations, rollcalls] = await Promise.all([
        getPrisoners(),
        getLocations(),
        getRollCalls()
      ]);
      
      prisonerCount = prisoners.length;
      locationCount = locations.length;
      recentRollCalls = rollcalls.slice(0, 5);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      loading = false;
    }
  });
</script>

<div class="min-h-screen bg-gray-50">
  <nav class="bg-white shadow">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <h1 class="text-2xl font-bold text-gray-900">Prison Roll Call System</h1>
        </div>
      </div>
    </div>
  </nav>
  
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    {#if loading}
      <p>Loading...</p>
    {:else}
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <StatCard 
          title="Prisoners" 
          count={prisonerCount} 
          link="/prisoners"
          data-testid="prisoners-stat"
        />
        <StatCard 
          title="Locations" 
          count={locationCount} 
          link="/locations"
          data-testid="locations-stat"
        />
      </div>
    {/if}
  </main>
</div>
```

### Component Example

```svelte
<!-- src/lib/components/StatCard.svelte -->
<script>
  export let title;
  export let count;
  export let link;
</script>

<a href={link} class="block bg-white rounded-lg shadow p-6 hover:shadow-lg transition">
  <h3 class="text-lg font-semibold text-gray-700">{title}</h3>
  <p class="text-3xl font-bold text-blue-600 mt-2">{count}</p>
  <span class="text-sm text-gray-500 mt-2 inline-block">View All →</span>
</a>
```

### API Service Example

```javascript
// src/lib/services/api.js
const API_BASE = 'http://localhost:8000/api/v1';

export async function getPrisoners() {
  const response = await fetch(`${API_BASE}/inmates`);
  if (!response.ok) throw new Error('Failed to fetch prisoners');
  return response.json();
}

export async function createPrisoner(data) {
  const response = await fetch(`${API_BASE}/inmates`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data)
  });
  if (!response.ok) throw new Error('Failed to create prisoner');
  return response.json();
}

export async function getLocations() {
  const response = await fetch(`${API_BASE}/locations`);
  if (!response.ok) throw new Error('Failed to fetch locations');
  return response.json();
}

export async function getRollCalls() {
  const response = await fetch(`${API_BASE}/rollcalls`);
  if (!response.ok) throw new Error('Failed to fetch roll calls');
  return response.json();
}
```

---

## Step 6: RUN TESTS

**Objective:** Run Vitest tests

```bash
npm test
```

**Expected:** Tests should start passing

---

## Step 7: ITERATE

**Objective:** Debug until all Vitest tests pass

**Common Issues:**
- **Import errors:** Check file paths
- **API mocking:** Ensure fetch is mocked correctly
- **Component props:** Verify prop types match
- **Async issues:** Use `await` properly in tests

**Debugging:**
```bash
# Run single test file
npm test -- PrisonerCard.test.js

# Run with coverage
npm test -- --coverage

# Watch mode
npm test -- --watch
```

---

## Step 8: BROWSER VERIFY

**Objective:** Use agent-browser to verify UI works in real browser

### Start Dev Server

```bash
# Terminal 1: Start SvelteKit dev server
npm run dev

# Wait for server to be ready
sleep 3
```

### Run Browser Tests

```bash
# Terminal 2: Run browser verification
./tests/browser/test_home_page.sh
```

### Advanced Browser Testing

```bash
#!/bin/bash
# tests/browser/test_prisoner_enrollment.sh

echo "Testing Prisoner Enrollment Flow..."

# Start browser
agent-browser open http://localhost:5173/prisoners/new

# Take initial snapshot
agent-browser snapshot -i --json > snapshot.json

# Fill form
agent-browser fill "@e1" "A12345"  # Inmate number
agent-browser fill "@e2" "John"    # First name
agent-browser fill "@e3" "Doe"     # Last name
agent-browser fill "@e4" "1990-01-01"  # DOB
agent-browser fill "@e5" "A"       # Cell block
agent-browser fill "@e6" "101"     # Cell number

# Submit form
agent-browser click "@e7"  # Submit button

# Wait for navigation
agent-browser wait --url "**/prisoners/*/enroll"

# Verify we're on enrollment page
agent-browser get url | grep -q "enroll" || exit 1
echo "✓ Navigated to enrollment page"

# Take screenshot
agent-browser screenshot tests/browser/screenshots/enrollment_page.png

# Check for errors
agent-browser errors
agent-browser console

# Cleanup
agent-browser close

echo "✓ Enrollment flow test passed"
```

### Camera Testing

```bash
#!/bin/bash
# tests/browser/test_camera_access.sh

echo "Testing Camera Access..."

# Note: Camera testing requires --headed mode or mock
agent-browser --headed open http://localhost:5173/prisoners/123/enroll

# Wait for camera permission prompt (manual in headed mode)
sleep 5

# Check if video element exists
agent-browser is visible "video" || exit 1
echo "✓ Video element found"

# Take screenshot showing camera preview
agent-browser screenshot tests/browser/screenshots/camera_preview.png

agent-browser close
```

---

## Step 9: REFACTOR

**Objective:** Improve code quality while keeping tests green

**Refactoring Checklist:**
- [ ] Extract repeated code into functions
- [ ] Use meaningful variable names
- [ ] Add TypeScript types (if using TS)
- [ ] Improve component composition
- [ ] Optimize API calls (caching, batching)
- [ ] Add loading states
- [ ] Add error handling
- [ ] Improve accessibility (ARIA labels)

**Example Refactoring:**

**Before:**
```svelte
<script>
  let data;
  fetch('http://localhost:8000/api/v1/inmates')
    .then(r => r.json())
    .then(d => data = d);
</script>
```

**After:**
```svelte
<script>
  import { onMount } from 'svelte';
  import { getPrisoners } from '$lib/services/api';
  
  let prisoners = [];
  let loading = true;
  let error = null;
  
  onMount(async () => {
    try {
      prisoners = await getPrisoners();
    } catch (err) {
      error = err.message;
    } finally {
      loading = false;
    }
  });
</script>

{#if loading}
  <p>Loading...</p>
{:else if error}
  <p class="text-red-600">Error: {error}</p>
{:else}
  <!-- Display prisoners -->
{/if}
```

---

## Step 10: FINAL CHECK

**Objective:** Run full test suite and capture artifacts

```bash
# 1. Run all Vitest tests
npm test -- --coverage

# 2. Run all browser tests
for test in tests/browser/test_*.sh; do
  echo "Running $test..."
  bash "$test" || exit 1
done

# 3. Check coverage report
open coverage/index.html

# 4. Review screenshots
ls -la tests/browser/screenshots/

# 5. Check for console errors
cat tests/browser/logs/*.txt
```

**Quality Gates:**
- ✅ All Vitest tests pass
- ✅ All browser tests pass
- ✅ Code coverage ≥80%
- ✅ No console errors
- ✅ Screenshots look correct
- ✅ Responsive design works (test multiple viewports)

---

## Step 11: UPDATE TODO

**Objective:** Mark progress in PROJECT_TODO.md

```markdown
#### Web UI 1.1: Home Page
- [x] 📋 Design Complete
- [x] 🏗️ Built
- [x] 🧪 Tests Created
- [x] ✅ All Tests Pass
```

---

## Step 12: COMMIT

**Objective:** Save work with clear commit message

```bash
git add .
git commit -m "feat(web-ui): implement home page with stats and navigation

- Add home page route (/)
- Create StatCard component
- Implement API service for prisoners/locations/rollcalls
- Add Vitest unit tests (95% coverage)
- Add agent-browser verification tests
- All tests passing

Closes #WEB-UI-1.1"

git push
```

---

## Testing Best Practices

### 1. Test Pyramid

```
        /\
       /  \      E2E (agent-browser)
      /____\     Few, high-value flows
     /      \
    /        \   Integration (Vitest)
   /__________\  Component interactions
  /            \
 /______________\ Unit (Vitest)
                  Many, fast tests
```

### 2. What to Test

**Unit Tests (Vitest):**
- Component rendering
- Props handling
- Event emissions
- Computed values
- API service functions
- Utility functions

**Browser Tests (agent-browser):**
- Critical user flows
- Form submissions
- Navigation
- Camera access
- Visual regression (screenshots)
- Console errors

### 3. Test Organization

```
tests/
├── unit/
│   ├── components/
│   │   ├── StatCard.test.js
│   │   ├── PrisonerCard.test.js
│   │   └── CameraView.test.js
│   ├── services/
│   │   └── api.test.js
│   └── utils/
│       └── camera.test.js
├── browser/
│   ├── test_home_page.sh
│   ├── test_prisoner_enrollment.sh
│   ├── test_rollcall_flow.sh
│   ├── screenshots/
│   ├── snapshots/
│   └── logs/
└── fixtures/
    └── mock_data.js
```

---

## agent-browser Cheat Sheet

### Essential Commands

```bash
# Navigation
agent-browser open http://localhost:5173
agent-browser reload

# Inspection
agent-browser snapshot -i              # Interactive elements
agent-browser snapshot -i --json       # JSON output
agent-browser get text "h1"
agent-browser get url

# Interaction
agent-browser click @e1
agent-browser fill @e2 "value"
agent-browser press Enter

# Verification
agent-browser is visible @e1
agent-browser is enabled @e2

# Debugging
agent-browser screenshot page.png
agent-browser console
agent-browser errors
agent-browser --headed open <url>      # Show browser

# Cleanup
agent-browser close
```

### Waiting for Elements

```bash
# Wait for element to appear
agent-browser wait @e1

# Wait for text
agent-browser wait --text "Success"

# Wait for URL
agent-browser wait --url "**/dashboard"

# Wait for network idle
agent-browser wait --load networkidle

# Simple delay
agent-browser wait 1000  # 1 second
```

---

## Continuous Integration

### GitHub Actions Example

```yaml
# .github/workflows/web-ui-tests.yml
name: Web UI Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Node
        uses: actions/setup-node@v3
        with:
          node-version: '20'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run Vitest tests
        run: npm test -- --coverage
      
      - name: Start dev server
        run: npm run dev &
        
      - name: Wait for server
        run: sleep 5
      
      - name: Run browser tests
        run: |
          for test in tests/browser/test_*.sh; do
            bash "$test"
          done
      
      - name: Upload screenshots
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: screenshots
          path: tests/browser/screenshots/
```

---

## Success Metrics

### Per TODO Item
- ✅ All 4 checkboxes marked
- ✅ Vitest tests written and passing
- ✅ agent-browser tests written and passing
- ✅ Code coverage ≥80%
- ✅ No console errors
- ✅ Screenshots captured
- ✅ Clean git commit

### Per Phase
- ✅ All items in phase complete
- ✅ Integration tests passing
- ✅ No regression in other phases
- ✅ Demo-ready quality

---

*Next document: `web-ui-api-mapping.md` for complete endpoint integration details*
