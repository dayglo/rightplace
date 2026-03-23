# POC Roll Call Mobile UI - Implementation Plan

## Created Structure

✅ **Folder structure created**: `/web-ui/src/routes/poc-rollcall-1/`

```
poc-rollcall-1/
├── +page.svelte                     # Landing page (redirects to roll call list)
├── README.md                        # POC documentation
└── rollcalls/
    ├── +page.svelte                 # Roll call list (mobile view) - TO CREATE
    ├── +page.ts                     # Data loader - TO CREATE
    └── [id]/
        ├── preview/
        │   ├── +page.svelte         # Preview screen - TO CREATE
        │   └── +page.ts             # Load roll call details - TO CREATE
        └── execute/
            ├── +page.svelte         # Main execution interface - TO CREATE
            ├── +page.ts             # Load roll call data - TO CREATE
            └── [components]         # Mobile-specific components - TO CREATE
```

## Access URLs

### Development
- **POC Home**: http://localhost:5173/poc-rollcall-1
- **Roll Call List**: http://localhost:5173/poc-rollcall-1/rollcalls
- **Preview**: http://localhost:5173/poc-rollcall-1/rollcalls/[id]/preview
- **Execute**: http://localhost:5173/poc-rollcall-1/rollcalls/[id]/execute

### Existing Admin UI (Untouched)
- **Admin Home**: http://localhost:5173/rollcalls
- **Admin Details**: http://localhost:5173/rollcalls/[id]

## Implementation Strategy

### Phase 1: Roll Call List (Mobile View)
**Files to create:**
- `rollcalls/+page.svelte` - Mobile-optimized card list
- `rollcalls/+page.ts` - Load roll calls from API

**Features:**
- Card-based layout (one per roll call)
- Color-coded status badges (scheduled, in_progress, completed)
- Quick stats (time, inmate count, stops)
- Filter by status
- Pull-to-refresh

### Phase 2: Preview Screen
**Files to create:**
- `rollcalls/[id]/preview/+page.svelte` - Preview UI
- `rollcalls/[id]/preview/+page.ts` - Load roll call details

**Features:**
- Route overview (stops, inmates per stop)
- Inmate list (grouped by location)
- Non-enrolled warnings
- Time estimate
- "Start Roll Call" button

### Phase 3: Execution Interface
**Files to create:**
- `rollcalls/[id]/execute/+page.svelte` - Main execution flow
- `rollcalls/[id]/execute/+page.ts` - Load and manage state
- `rollcalls/[id]/execute/CameraView.svelte` - Camera component
- `rollcalls/[id]/execute/InmateCard.svelte` - Current inmate display
- `rollcalls/[id]/execute/ScanFeedback.svelte` - Success/failure overlay
- `rollcalls/[id]/execute/ManualOverride.svelte` - Manual verification form
- `rollcalls/[id]/execute/StopSummary.svelte` - Stop completion screen
- `rollcalls/[id]/execute/CompletionSummary.svelte` - Final summary

**Features:**
- Camera-first interface
- Real-time scanning
- Progress tracking
- Manual override capability
- Stop-by-stop navigation
- Offline support (queued operations)

## Reused Services (No Modifications)

### API Client (`$lib/services/api.ts`)
```typescript
import {
  getRollCalls,          // List roll calls
  getRollCall,           // Get single roll call details
  startRollCall,         // Start execution
  completeRollCall,      // Mark complete
  verifyFace,            // Face recognition
  recordVerification,    // Record manual verification
  getRollCallVerifications // Get verification history
} from '$lib/services/api';
```

### Camera Service (`$lib/services/camera.ts`)
```typescript
import {
  getCamera,             // Initialize camera
  capturePhoto           // Capture image
} from '$lib/services/camera';
```

## Design Reference

All UI designs are documented in:
- `/web-ui-poc/pod-design.md` - Detailed UX specifications

## Testing Strategy

### Browser Testing
- Chrome DevTools mobile emulation
- iPhone SE (375px width)
- iPhone 12 Pro (390px width)
- iPad (768px width)
- Landscape mode

### Real Device Testing
- iOS Safari
- Android Chrome
- Camera permissions
- Offline mode
- Battery drain

## Key Technical Decisions

### 1. **Mobile-First Tailwind Classes**
```svelte
<div class="h-screen">           <!-- Full viewport height -->
<div class="fixed bottom-0">     <!-- Bottom navigation -->
<div class="touch-manipulation">  <!-- Touch optimization -->
<button class="min-h-[48px]">    <!-- Minimum touch target -->
```

### 2. **State Management**
- Use Svelte 5 runes (`$state`, `$derived`, `$props`)
- No external state management library needed
- Keep state local to each route

### 3. **Offline Support**
- Queue verifications in localStorage
- Sync when connection restored
- Visual indicators for offline mode

### 4. **Performance**
- Lazy load inmate photos
- Debounce camera captures
- Minimize re-renders during scanning

## Success Criteria

✅ **Functional Requirements:**
- [ ] Officer can view assigned roll calls
- [ ] Officer can preview route before starting
- [ ] Officer can scan inmates using camera
- [ ] System recognizes faces and records verification
- [ ] Officer can manually override failed scans
- [ ] System tracks progress through route
- [ ] Officer can complete roll call and view summary

✅ **Non-Functional Requirements:**
- [ ] Works on mobile browsers (iOS Safari, Android Chrome)
- [ ] Touch-optimized (minimum 48px targets)
- [ ] Fast (<3 seconds per verification)
- [ ] Works offline (queues operations)
- [ ] Battery efficient (camera optimized)

✅ **Code Quality:**
- [ ] Zero modifications to existing code
- [ ] TypeScript type safety
- [ ] Responsive design (mobile + tablet)
- [ ] Accessible (WCAG 2.1 AA)

## Next Steps

1. **Start Development Server**
   ```bash
   cd web-ui
   npm run dev
   ```

2. **Navigate to POC**
   ```
   http://localhost:5173/poc-rollcall-1
   ```

3. **Begin Phase 1: Roll Call List**
   - Create `rollcalls/+page.svelte`
   - Create `rollcalls/+page.ts`
   - Test mobile view

4. **Iterate Through Phases**
   - Build incrementally
   - Test on mobile devices
   - Gather feedback

## Removal Instructions

When POC is complete or needs to be removed:

```bash
# Delete entire POC folder
rm -rf web-ui/src/routes/poc-rollcall-1

# Or keep for future development
git checkout -b poc-rollcall-mobile
# Continue development on separate branch
```

## Notes

- This POC is completely isolated from existing admin UI
- Can be developed and tested without risk to production code
- Uses existing infrastructure (API client, camera service, Tailwind)
- Follows SvelteKit conventions and patterns
- Mobile-first, touch-optimized design
