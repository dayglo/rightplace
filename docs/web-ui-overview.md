# Prison Roll Call - Web UI Design Document

## Overview

This document specifies the design for a **SvelteKit-based web UI** that serves as an intermediate demo for the Prison Roll Call system. The web UI provides a customer-facing demonstration of the fully functional backend, focusing on core workflows without the complexity of React Native mobile development.

**Version:** 1.0  
**Date:** January 2026  
**Target:** Customer Demo with Cardboard Cutouts

---

## Executive Summary

The web UI enables prison officers to:
1. **Enroll new prisoners** with face recognition
2. **Create new locations** (cells, blocks, common areas)
3. **Create roll calls** with ordered location routes
4. **Start roll calls** and navigate through locations
5. **Verify prisoners** are in the right place using webcam
6. **View detailed reports** showing roll call results

**Key Technologies:**
- **Frontend:** SvelteKit + Tailwind CSS
- **Backend:** Existing FastAPI server (fully functional)
- **Testing:** Vitest + agent-browser CLI automation
- **Camera:** Browser MediaDevices API (getUserMedia)

---

## Design Principles

### 1. Customer Demo Ready
- **Professional appearance** with Tailwind CSS styling
- **Smooth workflows** that showcase the technology
- **Clear visual feedback** at every step
- **Error handling** that doesn't break the demo flow

### 2. Webcam-First Verification
- **Continuous frame capture** (Option A with twist)
- **Real-time feedback** showing detection quality
- **Auto-stop on match** when confidence threshold met
- **Manual override** available when needed

### 3. Simplified for Demo
- **5 prisoners maximum** (cardboard cutouts)
- **Simple location hierarchy** (no complex facility structure)
- **Linear roll call routes** (ordered list of locations)
- **Detailed reporting** to show system capabilities

---

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                    BROWSER (Web UI)                     │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           SvelteKit Application                  │  │
│  │                                                  │  │
│  │  • Pages (routes)                                │  │
│  │  • Components (Tailwind styled)                  │  │
│  │  • Stores (state management)                     │  │
│  │  • Camera service (getUserMedia)                 │  │
│  │  • API client (fetch to FastAPI)                 │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │           Browser APIs                           │  │
│  │                                                  │  │
│  │  • MediaDevices.getUserMedia() → Webcam          │  │
│  │  • Canvas API → Frame capture                    │  │
│  │  • Fetch API → HTTP requests                     │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
                          ↓ HTTP/REST
┌─────────────────────────────────────────────────────────┐
│              FastAPI Server (Existing)                  │
│                                                         │
│  • Face detection (DeepFace)                            │
│  • Face recognition (Facenet512)                        │
│  • Inmate/Location/RollCall CRUD                        │
│  • Verification recording                               │
└─────────────────────────────────────────────────────────┘
```

### Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Framework** | SvelteKit | SSR, routing, forms, server actions |
| **Styling** | Tailwind CSS | Utility-first responsive design |
| **State** | Svelte stores | Reactive state management |
| **Testing** | Vitest | Unit tests for components/logic |
| **E2E Testing** | agent-browser | Automated UI verification |
| **Camera** | getUserMedia | Webcam access for face capture |
| **HTTP Client** | Fetch API | Communication with FastAPI backend |

---

## User Roles

For the demo, we have a single user role:

**Prison Officer (Guard)**
- Enrolls new prisoners
- Creates locations and roll calls
- Conducts roll calls with webcam verification
- Reviews roll call reports

*Note: No authentication required for demo - single-user system*

---

## Core Workflows

### 1. Prisoner Enrollment
```
Officer → Prisoners Page → "Add Prisoner" 
  → Fill form (name, number, cell) 
  → "Enroll Face" 
  → Webcam activates 
  → Capture photo 
  → Server validates quality 
  → Success/Retry feedback
```

### 2. Location Creation
```
Officer → Locations Page → "Add Location"
  → Fill form (name, type, building, floor)
  → Submit
  → Location appears in list
```

### 3. Roll Call Creation
```
Officer → Roll Calls Page → "Create Roll Call"
  → Name roll call
  → Select locations (ordered)
  → System auto-assigns expected prisoners per location
  → Schedule time
  → Save
```

### 4. Conducting Roll Call
```
Officer → Active Roll Call → Start
  → Navigate to first location
  → Webcam activates (continuous scanning)
  → Point at prisoner
  → System detects face → matches → shows result
  → Officer confirms or manual override
  → Move to next location
  → Repeat until complete
  → View summary report
```

### 5. Viewing Reports
```
Officer → Roll Call History → Select roll call
  → View detailed report:
    - Each location visited
    - Each prisoner verified
    - Confidence scores
    - Timestamps
    - Manual overrides
    - Photos (optional)
```

---

## Webcam Verification Flow (Detailed)

### Continuous Frame Capture Approach

**How it works:**
1. Officer navigates to a location in the roll call
2. Webcam activates and shows live preview
3. System captures frames at intervals (every 500ms)
4. Each frame is sent to `/verify/quick` endpoint
5. Server responds with match result and confidence
6. UI shows real-time feedback:
   - "Scanning..." (no face detected)
   - "Detecting..." (face found, processing)
   - "Match: John Doe (89%)" (match found)
   - "No match" (below threshold)
7. When match found above threshold, capture stops
8. Officer can confirm or retry

**Implementation Details:**
```javascript
// Pseudo-code for verification loop
let isScanning = true;
let lastRequestTime = 0;
const SCAN_INTERVAL = 500; // ms

async function scanLoop() {
  if (!isScanning) return;
  
  const now = Date.now();
  if (now - lastRequestTime < SCAN_INTERVAL) {
    requestAnimationFrame(scanLoop);
    return;
  }
  
  // Capture frame from video element
  const frame = captureFrame(videoElement);
  
  // Send to server (don't wait for response)
  lastRequestTime = now;
  verifyFrame(frame, currentLocation, rollCallId)
    .then(result => {
      updateUI(result);
      if (result.matched && result.confidence > 0.75) {
        isScanning = false;
        showConfirmation(result);
      }
    })
    .catch(err => {
      // Continue scanning on error
      console.error(err);
    });
  
  requestAnimationFrame(scanLoop);
}
```

**Benefits:**
- Natural "scanning" experience
- No overwhelming the server (500ms intervals)
- Continues until match found
- Handles errors gracefully
- Works with existing backend

---

## Next Steps

This overview document is part 1 of the web UI design documentation. The following documents provide detailed specifications:

1. **web-ui-overview.md** (this document) - Architecture and workflows
2. **web-ui-screens.md** - Detailed screen specifications and layouts
3. **web-ui-api-mapping.md** - Backend endpoint integration
4. **web-ui-iteration-loop.md** - TDD workflow with agent-browser testing
5. **web-ui-components.md** - Reusable component library

---

*See next document: `web-ui-screens.md` for detailed screen specifications*
