# POC Roll Call - Execution Interface

## Overview

This is a **Proof of Concept (POC)** for a web-based roll call execution interface. It is completely isolated from the existing admin UI and can be safely removed without affecting existing functionality.

**Target Devices**: This runs in any modern web browser (desktop, tablet, or mobile phone).

## Structure

```
poc-rollcall-1/
├── README.md                        # This file
├── +layout.svelte                   # POC-specific layout
└── rollcalls/
    ├── +page.svelte                 # Roll call list (view)
    ├── +page.ts                     # Data loader
    └── [id]/
        ├── preview/
        │   ├── +page.svelte         # Preview route and inmates before starting
        │   └── +page.ts             # Load roll call details
        └── execute/
            ├── +page.svelte         # Main execution interface
            ├── +page.ts             # Load roll call data
            ├── CameraView.svelte    # Camera scanning component
            ├── InmateCard.svelte    # Current inmate display
            ├── ScanFeedback.svelte  # Success/failure overlay
            ├── ManualOverride.svelte # Manual verification form
            └── CompletionSummary.svelte # Final summary screen
```

## URL Routes

### Existing Admin UI (Untouched)
- `/rollcalls` - Admin roll call list
- `/rollcalls/[id]` - Admin roll call details
- `/rollcalls/new` - Create new roll call

### POC UI (New)
- `/poc-rollcall-1/rollcalls` - roll call list
- `/poc-rollcall-1/rollcalls/[id]/preview` - Preview before execution
- `/poc-rollcall-1/rollcalls/[id]/execute` - Execute roll call

## Shared Services

This POC reuses existing infrastructure without modification:

```typescript
// API Client
import {
  getRollCall,
  startRollCall,
  completeRollCall,
  verifyFace,
  recordVerification
} from '$lib/services/api';

// Camera Service
import { getCamera, capturePhoto } from '$lib/services/camera';
```

## Design Specification

See `/web-ui-poc/pod-design.md` for detailed UX design specifications.

## Development

### Access the POC
```bash
# Start dev server
cd web-ui
npm run dev

# Navigate to:
http://localhost:5173/poc-rollcall-1/rollcalls
```

### Testing
- Chrome DevTools: Toggle Device Toolbar (Cmd+Shift+M)
- Test on: iPhone SE (375px), iPhone 12 Pro (390px), iPad (768px)

## Isolation Guarantee

✅ **Zero modifications to existing code**
- No changes to `/routes/rollcalls` (existing admin UI)
- No changes to `/routes/prisoners` or `/routes/locations`
- No changes to existing components or services
- Only imports from `$lib/services/*` (read-only usage)

✅ **Easy removal**
```bash
# When POC is complete
rm -rf web-ui/src/routes/poc-rollcall-1
```

## Technology Stack

- **Framework**: SvelteKit with Svelte 5 (runes)
- **Styling**: Tailwind CSS v4 (utilities)
- **TypeScript**: Full type safety
- **API Client**: Shared with existing admin UI
- **Camera Access**: MediaDevices Web API (via existing camera service)

## Implementation Status

- [ ] Roll call list view
- [ ] Roll call preview screen
- [ ] Main execution interface
- [ ] Camera scanning component
- [ ] Scan result feedback
- [ ] Manual override form
- [ ] Stop completion summary
- [ ] Roll call completion screen

## Notes

- This POC follows the design spec in `web-ui-poc/pod-design.md`
- All new files are contained within `poc-rollcall-1/` folder
- Can coexist with existing admin UI indefinitely
- Designed for browsers (Safari iOS, Chrome Android)
