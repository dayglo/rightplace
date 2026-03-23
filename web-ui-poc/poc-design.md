# Roll Call Mobile Web UI - UX Design Document

## Core UX Principles

1. **Speed-first**: Complete verification in <3 seconds per inmate
2. **One-handed mobile operation**: All critical actions thumb-reachable
3. **Progressive disclosure**: Show only what's needed at each step
4. **Offline-resilient**: Queue operations, sync when connected
5. **Error-tolerant**: Easy recovery from failed scans

---

## Recommended Flow Architecture

### Flow Overview
```
1. Roll Call Selection → 2. Preview/Route Review → 3. Execute Roll Call
   → 4. Per-Stop Verification → 5. Completion Summary
```

---

## Screen-by-Screen Design Suggestions

### 1. Roll Call Selection Screen

**Purpose**: Officer picks which roll call to execute

**Layout Concept:**
- **Card-based list** with color-coded status badges
- **Critical info only**: Time, location, inmate count
- **Single action button**: "Start" (scheduled) or "View Details" (future)

**Card Content:**
```
┌─────────────────────────────────┐
│ 🔴 URGENT • 08:00              │
│ A Wing - Morning Roll Call      │
│ 3 stops • 45 inmates            │
│ Assigned to: Officer Badge #123 │
│         [START NOW]             │
└─────────────────────────────────┘
```

**Visual Hierarchy:**
- **Red badge**: Overdue/current
- **Amber badge**: Coming up (within 1 hour)
- **Gray badge**: Scheduled for later
- **Green badge**: Completed

**Key Features:**
- Filter by status (scheduled/in-progress/completed)
- Search by location/wing
- Pull-to-refresh for latest data

---

### 2. Roll Call Preview Screen

**Purpose**: Review route and inmates before starting (confidence builder)

**Two-Tab Layout:**

**Tab 1: Route Overview**
```
┌─────────────────────────────────┐
│ A Wing Morning Roll Call        │
│ [Route] [Inmates]               │
├─────────────────────────────────┤
│ 📍 YOUR ROUTE                   │
│                                 │
│ 1️⃣ A Wing - Landing 1           │
│    └─ 15 inmates (cells A1-01..15)│
│    └─ ⚠️ 1 not enrolled          │
│                                 │
│ 2️⃣ A Wing - Landing 2           │
│    └─ 18 inmates (cells A2-01..18)│
│    └─ ✓ All enrolled            │
│                                 │
│ 3️⃣ Healthcare Unit              │
│    └─ 12 inmates (temporary)    │
│    └─ ⚠️ 2 not enrolled          │
│                                 │
│ ⏱️ Est. time: 12 minutes         │
│                                 │
│    [< BACK]  [START ROLL CALL >]│
└─────────────────────────────────┘
```

**Tab 2: Inmate List**
```
┌─────────────────────────────────┐
│ A Wing Morning Roll Call        │
│ [Route] [Inmates]               │
├─────────────────────────────────┤
│ 📋 45 INMATES                   │
│                                 │
│ 🔍 Search inmates...            │
│                                 │
│ Landing 1 (15)                  │
│ ├─ ✓ SMITH, John (#12345)      │
│ ├─ ⚠️ JONES, Sarah (not enrolled)│
│ ├─ ✓ BROWN, Tom (#12347)       │
│ └─ ...12 more                   │
│                                 │
│ Landing 2 (18)                  │
│ ├─ ✓ WILSON, Amy (#12360)      │
│ └─ ...17 more                   │
│                                 │
│    [< BACK]  [START ROLL CALL >]│
└─────────────────────────────────┘
```

**Key Features:**
- Visual warning for non-enrolled inmates (manual verification required)
- Collapsible sections to reduce cognitive load
- Time estimate based on historical data + connection travel times
- Option to customize route (reorder stops)

---

### 3. Active Roll Call - Main Interface

**Purpose**: Fast, frictionless verification flow

**Design Option A: "Camera-First" (Recommended for Mobile)**

```
┌─────────────────────────────────┐
│ Stop 1/3: A Wing Landing 1      │
│ ● 4/15 verified    [Skip Stop ⏭️]│
├─────────────────────────────────┤
│                                 │
│        📸 CAMERA VIEW           │
│     ┌─────────────────┐         │
│     │                 │         │
│     │  Live Camera    │         │
│     │   Viewfinder    │         │
│     │                 │         │
│     │  [TAP TO SCAN]  │         │
│     └─────────────────┘         │
│                                 │
│ 👤 NEXT EXPECTED:               │
│                                 │
│ ┌─────────────────────────────┐ │
│ │ SMITH, John                 │ │
│ │ Cell: A1-05 • #12345        │ │
│ │ [✓ MANUAL]  [SKIP]  [ABSENT]│ │
│ └─────────────────────────────┘ │
│                                 │
│ Remaining (11): Jones, Brown... │
│                                 │
│ [PAUSE ROLL CALL] [NEXT STOP →] │
└─────────────────────────────────┘
```

**Design Option B: "List-First" (Better for Tablets/Systematic Approach)**

```
┌──────────────┬──────────────────┐
│   📸 SCAN    │ Stop 1/3: A1     │
│   ┌────────┐ │ ● 4/15 verified  │
│   │        │ │                  │
│   │ Camera │ │ ✅ SMITH, John   │
│   │ View   │ │ ✅ JONES, Sarah  │
│   │        │ │ ✅ BROWN, Tom    │
│   └────────┘ │ ✅ DAVIS, Mike   │
│              │                  │
│  [SCAN NOW]  │ ⏺️ WILSON, Amy   │
│              │    [MANUAL][SKIP]│
│              │                  │
│              │ ⏸️ LEE, Chris     │
│              │ ⏸️ TAYLOR, Pat   │
│              │ ⏸️ ...9 more     │
│              │                  │
│              │ [NEXT STOP →]    │
└──────────────┴──────────────────┘
```

**Key Design Elements:**

1. **Persistent Progress Bar** (Top):
   - Shows stop progress (1/3)
   - Shows inmate progress at current stop (4/15)
   - Elapsed time

2. **Large Camera Button**:
   - Center of screen
   - Finger/thumb optimized size (minimum 80x80px)
   - Provides visual feedback on tap

3. **Next Expected Inmate Card**:
   - Shows who should be scanned next
   - Displays photo (if available) for visual confirmation
   - Quick action buttons for edge cases

4. **Smart Ordering Logic**:
   - Default: Cell order (A1-01, A1-02, A1-03...)
   - Alternative: Alphabetical by last name
   - Officer can scan in any order (system adapts)

5. **Quick Actions** (swipe gestures optional):
   - Swipe right on inmate card: Skip
   - Swipe left: Mark absent
   - Long press: Manual override

---

### 4. Scan Result Feedback Screens

**Success State (Auto-advance in 1 second):**
```
┌─────────────────────────────────┐
│                                 │
│         ✅ VERIFIED              │
│                                 │
│      👤 SMITH, John             │
│      #12345 • Cell A1-05        │
│                                 │
│      Confidence: 96%            │
│      ✓ At expected location     │
│                                 │
│   [Continuing in 1s...]         │
│                                 │
└─────────────────────────────────┘
```

**Failure State (Requires Decision):**
```
┌─────────────────────────────────┐
│         ❌ MISMATCH              │
│                                 │
│  Expected: SMITH, John          │
│  Detected: JONES, Sarah         │
│  Confidence: 87%                │
│                                 │
│  Possible issues:               │
│  • Wrong inmate scanned         │
│  • Inmate at wrong location     │
│                                 │
│  [RE-SCAN]      [MANUAL CHECK]  │
│  [MARK WRONG LOCATION] [SKIP]   │
└─────────────────────────────────┘
```

**Quality Issue State (Guidance):**
```
┌─────────────────────────────────┐
│      ⚠️ POOR IMAGE QUALITY       │
│                                 │
│  Issues detected:               │
│  🌙 Low lighting                │
│  📏 Face too far from camera    │
│                                 │
│  💡 Suggestions:                │
│  • Turn on flash/torch          │
│  • Move closer (1-2 meters)     │
│  • Ask inmate to look up        │
│                                 │
│  [TRY AGAIN]  [MANUAL OVERRIDE] │
└─────────────────────────────────┘
```

**Key Features:**
- **Color-coded backgrounds**: Green (success), red (error), amber (warning)
- **Haptic feedback**: Vibration on success/failure
- **Audio cues** (optional): Beep on success
- **Auto-advance**: Success screens auto-dismiss after 1 second
- **Actionable**: Clear next steps for errors

---

### 5. Manual Override/Check Screen

**Purpose**: Handle edge cases (poor lighting, facial injury, non-enrolled)

```
┌─────────────────────────────────┐
│ ← Manual Verification           │
├─────────────────────────────────┤
│ 👤 SMITH, John                  │
│ #12345 • Cell A1-05             │
│ DOB: 15/03/1985 • Age: 39       │
│                                 │
│ ┌─────────────────────────────┐ │
│ │    [Enrollment Photo]       │ │
│ │    (if available)           │ │
│ └─────────────────────────────┘ │
│                                 │
│ ✓ Visually confirmed present?   │
│                                 │
│ ⚠️ Reason for manual override:  │
│ ⚪ Facial injury/bandage        │
│ ⚪ Poor lighting conditions      │
│ ⚪ Camera/technical failure      │
│ ⚪ Inmate not enrolled yet       │
│ ⚪ Other (specify below)         │
│                                 │
│ Optional notes:                 │
│ ┌───────────────────────────┐   │
│ │                           │   │
│ └───────────────────────────┘   │
│                                 │
│  [CANCEL]    [CONFIRM PRESENT] │
└─────────────────────────────────┘
```

**Key Features:**
- Shows inmate photo for comparison
- **Required reason selection** (audit trail)
- Optional notes for context
- Clear confirmation required
- **Warning**: Manual overrides flagged in reports

---

### 6. Stop Completion Screen

**Purpose**: Review stop before moving to next location

```
┌─────────────────────────────────┐
│ ✅ A Wing Landing 1 Complete    │
├─────────────────────────────────┤
│ ✅ Verified: 13/15 (87%)        │
│ ⚠️ Manual: 2                    │
│ ❌ Absent: 0                    │
│                                 │
│ Time taken: 4m 23s              │
│                                 │
│ 📋 BREAKDOWN:                   │
│ ✅ SMITH, John (face scan)      │
│ ✅ JONES, Sarah (face scan)     │
│ ⚠️ BROWN, Tom (manual)          │
│ ⚠️ DAVIS, Mike (manual)         │
│ ...9 more verified              │
│                                 │
│ ⚠️ Issues:                      │
│ • 2 manual overrides required   │
│   (poor lighting)               │
│                                 │
│ [← FIX ISSUES]                  │
│ [NEXT: Landing 2 (18 inmates) →]│
└─────────────────────────────────┘
```

**Key Features:**
- Quick stats at a glance
- Expandable list of all verifications
- Highlights issues/anomalies
- Option to go back and fix
- Shows next stop preview

---

### 7. Roll Call Completion Screen

**Purpose**: Final summary and submission

```
┌─────────────────────────────────┐
│ 🎉 Roll Call Complete!          │
├─────────────────────────────────┤
│ A Wing Morning Roll Call        │
│ Started: 08:02 • Ended: 08:14   │
│ Duration: 11 minutes 45 seconds │
│                                 │
│ 📊 OVERALL RESULTS              │
│ ✅ Verified: 41/45 (91%)        │
│ ⚠️ Manual: 3 (7%)               │
│ ❌ Absent: 1 (2%)               │
│                                 │
│ 📍 BY LOCATION                  │
│ ✅ Landing 1: 13/15             │
│ ✅ Landing 2: 16/18             │
│ ✅ Healthcare: 12/12            │
│                                 │
│ ⚠️ REQUIRES ATTENTION           │
│ • WILSON, David - ABSENT        │
│   (Cell A2-08)                  │
│   Action: Report to supervisor  │
│                                 │
│ [VIEW DETAILED REPORT]          │
│ [SUBMIT & FINISH] →             │
└─────────────────────────────────┘
```

**Key Features:**
- Clear success messaging
- Performance metrics (time, completion rate)
- Per-location breakdown
- Flagged issues for follow-up
- Export/print option for paper trail

---

## Additional UX Enhancements

### 1. Navigation Pattern

**Bottom Tab Bar** (persistent, thumb-optimized):
```
┌─────────────────────────────────┐
│     Content area                │
├─────────────────────────────────┤
│ [📋 Rolls] [📸 Scan] [📊 Reports]│
└─────────────────────────────────┘
```

### 2. Status Indicators

**Top Banner** (contextual):
```
┌─────────────────────────────────┐
│ 📶 Offline • 3 queued | 🔋 45%  │
└─────────────────────────────────┘
```

### 3. Gestures (Optional Enhancement)

- **Pull down**: Refresh roll call list
- **Swipe right on inmate**: Skip
- **Swipe left on inmate**: Mark absent
- **Long press camera**: Switch camera (front/back)
- **Shake device**: Undo last action

### 4. Offline Mode

```
┌─────────────────────────────────┐
│ ⚠️ Working Offline              │
│ 5 verifications queued          │
│ Will sync when connected        │
│ [VIEW QUEUE]                    │
└─────────────────────────────────┘
```

### 5. Dark Mode (Auto-enable in low light)

- Reduces screen glare in cells
- Saves battery on OLED screens
- Toggle in settings

### 6. Accessibility

- **Large touch targets**: Minimum 48x48px
- **High contrast mode**: For outdoor use
- **Voice feedback**: Optional audio confirmation
- **Haptic feedback**: Success/failure vibrations
- **Font scaling**: Respects system settings

---

## Information Architecture

```
Home
├─ Roll Call List
│  └─ Filter/Search
│
├─ Roll Call Preview
│  ├─ Route Tab
│  └─ Inmates Tab
│
├─ Active Roll Call
│  ├─ Stop 1
│  │  ├─ Scan Interface
│  │  ├─ Manual Override
│  │  ├─ Scan Results
│  │  └─ Stop Summary
│  │
│  ├─ Stop 2 (repeat)
│  ├─ Stop 3 (repeat)
│  └─ Completion Summary
│
└─ Reports/History
   ├─ Past Roll Calls
   └─ Individual Reports
```

---

## Mobile Optimization Considerations

### 1. Battery Management
- Reduce camera polling frequency when idle
- Warn at <20% battery
- Option to reduce screen brightness

### 2. Network Resilience
- Queue all operations locally
- Sync in background when connected
- Visual indicator of sync status

### 3. Performance
- Lazy load inmate photos
- Cache face embeddings locally
- Minimize re-renders during scanning

### 4. Screen Sizes
- Mobile (320px-480px): Single column, stack layout
- Tablet (768px+): Two-column layout where appropriate
- Landscape mode: Split screen (camera left, list right)

---

## Key Design Rationale

✅ **Location-centric**: Matches the `RouteStop` model structure
✅ **Flexible order**: Officers can scan inmates in any sequence within a stop
✅ **Minimal taps**: Camera is primary interaction, everything else is fallback
✅ **Audit-friendly**: Manual overrides require documented reasons
✅ **Resume-capable**: Roll calls can be paused/resumed (status persisted)
✅ **Error-tolerant**: Clear recovery paths for all failure modes

---

## Backend Integration Notes

### Models Used
- `RollCall`: Main roll call entity with status tracking
- `RouteStop`: Individual stops in the route with expected inmates
- `Verification`: Individual verification records
- `Inmate`: Prisoner records with enrollment status
- `Location`: Physical locations in hierarchy

### Repository Functions Required
- `RollCallRepository`: CRUD for roll calls, status updates, route stop updates
- `VerificationRepository`: Record verifications, count by status
- `InmateRepository`: Get inmates by location, enrollment status
- `LocationRepository`: Get location hierarchy, children
- `AuditRepository`: Log all manual overrides and critical actions

### API Endpoints Needed
- `GET /api/rollcalls` - List roll calls (filtered by officer/status)
- `GET /api/rollcalls/{id}` - Get roll call details
- `PUT /api/rollcalls/{id}/status` - Update roll call status
- `PUT /api/rollcalls/{id}/route/stops/{stop_id}` - Update stop status
- `POST /api/verifications` - Record verification
- `GET /api/inmates?location_id={id}` - Get inmates at location
- `POST /api/audit` - Log audit events
