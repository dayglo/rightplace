# Web UI Screen Specifications

## Navigation Structure

```
┌─────────────────────────────────────────────────────────┐
│                    Main Navigation                      │
│  Home | Prisoners | Locations | Roll Calls | Reports   │
└─────────────────────────────────────────────────────────┘
```

**Routes:**
- `/` - Home/Dashboard
- `/prisoners` - Prisoner list
- `/prisoners/new` - Add new prisoner
- `/prisoners/[id]` - Prisoner detail
- `/prisoners/[id]/enroll` - Face enrollment
- `/locations` - Location list
- `/locations/new` - Add new location
- `/rollcalls` - Roll call list
- `/rollcalls/new` - Create roll call
- `/rollcalls/[id]` - Roll call detail/report
- `/rollcalls/[id]/active` - Active roll call (conducting)

---

## Screen 1: Home/Dashboard

**Route:** `/`

**Purpose:** Landing page with quick stats and actions

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Prison Roll Call System                    [Server: ●] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  ┌─────────────────┐  ┌─────────────────┐             │
│  │  Prisoners      │  │  Locations      │             │
│  │  5 enrolled     │  │  8 total        │             │
│  │  [View All]     │  │  [View All]     │             │
│  └─────────────────┘  └─────────────────┘             │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Recent Roll Calls                              │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │ Morning Roll Call - Completed             │  │   │
│  │  │ 5/5 verified | Jan 28, 9:00 AM            │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  │  ┌───────────────────────────────────────────┐  │   │
│  │  │ Evening Roll Call - In Progress           │  │   │
│  │  │ 2/5 verified | Jan 28, 5:00 PM            │  │   │
│  │  └───────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Quick Actions                                  │   │
│  │  [+ New Prisoner] [+ New Location]              │   │
│  │  [+ Create Roll Call] [View Reports]            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Components
- **StatCard** - Shows count with icon and link
- **RollCallCard** - Recent roll call summary
- **QuickActionButton** - Large button for common actions

### Backend Endpoints
- `GET /api/v1/inmates` - Get prisoner count
- `GET /api/v1/locations` - Get location count
- `GET /api/v1/rollcalls` - Get recent roll calls

### Tailwind Styling
```html
<div class="min-h-screen bg-gray-50">
  <nav class="bg-white shadow">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <h1 class="text-2xl font-bold text-gray-900">Prison Roll Call</h1>
        </div>
        <div class="flex items-center">
          <span class="flex items-center text-sm text-gray-600">
            Server: <span class="ml-2 h-3 w-3 rounded-full bg-green-500"></span>
          </span>
        </div>
      </div>
    </div>
  </nav>
  
  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
    <!-- Stats Grid -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
      <!-- Stat cards -->
    </div>
    
    <!-- Recent Roll Calls -->
    <div class="bg-white rounded-lg shadow p-6 mb-8">
      <!-- Roll call list -->
    </div>
    
    <!-- Quick Actions -->
    <div class="bg-white rounded-lg shadow p-6">
      <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
        <!-- Action buttons -->
      </div>
    </div>
  </main>
</div>
```

---

## Screen 2: Prisoner List

**Route:** `/prisoners`

**Purpose:** View all prisoners and their enrollment status

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Prisoners                          [+ Add Prisoner]    │
├─────────────────────────────────────────────────────────┤
│  Search: [____________]  Filter: [All ▼]                │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │ [Photo] John Doe                          ✓     │   │
│  │         #A12345 | Block A, Cell 101              │   │
│  │         Enrolled: Jan 27, 2026                   │   │
│  │         [View] [Enroll Face]                     │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [Photo] Jane Smith                        ✓     │   │
│  │         #A12346 | Block A, Cell 102              │   │
│  │         Enrolled: Jan 27, 2026                   │   │
│  │         [View] [Enroll Face]                     │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ [?]     Mike Johnson                      ✗     │   │
│  │         #A12347 | Block B, Cell 201              │   │
│  │         Not enrolled                             │   │
│  │         [View] [Enroll Face]                     │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Components
- **PrisonerCard** - Shows prisoner info with enrollment status
- **SearchBar** - Filter prisoners by name/number
- **FilterDropdown** - Filter by enrollment status

### Backend Endpoints
- `GET /api/v1/inmates` - List all prisoners

### Tailwind Styling
```html
<div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
  <div class="flex justify-between items-center mb-6">
    <h1 class="text-3xl font-bold text-gray-900">Prisoners</h1>
    <a href="/prisoners/new" 
       class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg">
      + Add Prisoner
    </a>
  </div>
  
  <div class="bg-white rounded-lg shadow p-6 mb-6">
    <div class="flex gap-4">
      <input type="text" placeholder="Search..." 
             class="flex-1 border border-gray-300 rounded-lg px-4 py-2" />
      <select class="border border-gray-300 rounded-lg px-4 py-2">
        <option>All</option>
        <option>Enrolled</option>
        <option>Not Enrolled</option>
      </select>
    </div>
  </div>
  
  <div class="space-y-4">
    <!-- Prisoner cards -->
  </div>
</div>
```

---

## Screen 3: Add Prisoner

**Route:** `/prisoners/new`

**Purpose:** Create new prisoner record

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Add New Prisoner                          [← Back]     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │  Prisoner Information                           │   │
│  │                                                  │   │
│  │  Inmate Number *                                │   │
│  │  [A_____]                                        │   │
│  │                                                  │   │
│  │  First Name *                                    │   │
│  │  [_________]                                     │   │
│  │                                                  │   │
│  │  Last Name *                                     │   │
│  │  [_________]                                     │   │
│  │                                                  │   │
│  │  Date of Birth *                                 │   │
│  │  [MM/DD/YYYY]                                    │   │
│  │                                                  │   │
│  │  Cell Block *                                    │   │
│  │  [A ▼]                                           │   │
│  │                                                  │   │
│  │  Cell Number *                                   │   │
│  │  [___]                                           │   │
│  │                                                  │   │
│  │  [Cancel]                    [Create Prisoner]  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Form Validation
- All fields required
- Inmate number must be unique
- Date of birth must be valid date
- Cell block/number must exist

### Backend Endpoints
- `POST /api/v1/inmates` - Create prisoner

### SvelteKit Form Action
```javascript
// +page.server.js
export const actions = {
  default: async ({ request }) => {
    const data = await request.formData();
    const inmateData = {
      inmate_number: data.get('inmate_number'),
      first_name: data.get('first_name'),
      last_name: data.get('last_name'),
      date_of_birth: data.get('date_of_birth'),
      cell_block: data.get('cell_block'),
      cell_number: data.get('cell_number')
    };
    
    const response = await fetch('http://localhost:8000/api/v1/inmates', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(inmateData)
    });
    
    if (response.ok) {
      const inmate = await response.json();
      throw redirect(303, `/prisoners/${inmate.id}/enroll`);
    }
    
    return { success: false, error: 'Failed to create prisoner' };
  }
};
```

---

## Screen 4: Face Enrollment

**Route:** `/prisoners/[id]/enroll`

**Purpose:** Capture and enroll prisoner's face

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Enroll Face: John Doe (#A12345)          [← Back]     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │                                                  │   │
│  │         ┌─────────────────────────┐             │   │
│  │         │                         │             │   │
│  │         │   [WEBCAM PREVIEW]      │             │   │
│  │         │                         │             │   │
│  │         │   [Face detection       │             │   │
│  │         │    overlay box]         │             │   │
│  │         │                         │             │   │
│  │         └─────────────────────────┘             │   │
│  │                                                  │   │
│  │  Status: Ready to capture                       │   │
│  │  Quality: Good ✓                                │   │
│  │                                                  │   │
│  │         [Capture Photo]                         │   │
│  │                                                  │   │
│  │  Instructions:                                  │   │
│  │  • Position face in center of frame             │   │
│  │  • Ensure good lighting                         │   │
│  │  • Look directly at camera                      │   │
│  │  • Remove glasses if possible                   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### States
1. **Initializing** - Requesting camera permission
2. **Ready** - Camera active, waiting for capture
3. **Capturing** - Photo taken, sending to server
4. **Success** - Enrollment successful
5. **Error** - Quality too low, retry needed

### Backend Endpoints
- `POST /api/v1/enrollment/{inmate_id}` - Enroll face (multipart/form-data)

### Camera Implementation
```javascript
// Camera service
let videoStream = null;

export async function startCamera(videoElement) {
  try {
    videoStream = await navigator.mediaDevices.getUserMedia({
      video: {
        width: { ideal: 1280 },
        height: { ideal: 720 },
        facingMode: 'user'
      }
    });
    videoElement.srcObject = videoStream;
    return { success: true };
  } catch (error) {
    return { success: false, error: error.message };
  }
}

export function captureFrame(videoElement) {
  const canvas = document.createElement('canvas');
  canvas.width = videoElement.videoWidth;
  canvas.height = videoElement.videoHeight;
  const ctx = canvas.getContext('2d');
  ctx.drawImage(videoElement, 0, 0);
  return canvas.toDataURL('image/jpeg', 0.8);
}

export function stopCamera() {
  if (videoStream) {
    videoStream.getTracks().forEach(track => track.stop());
    videoStream = null;
  }
}
```

---

## Screen 5: Location List

**Route:** `/locations`

**Purpose:** View and manage facility locations

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Locations                          [+ Add Location]    │
├─────────────────────────────────────────────────────────┤
│  Filter: [All Types ▼]  Building: [All ▼]              │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🏢 Block A                                       │   │
│  │    Building: Main | Floor: 1 | Capacity: 50     │   │
│  │    [Edit] [Delete]                               │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🚪 Cell A-101                                    │   │
│  │    Building: Main | Floor: 1 | Capacity: 1      │   │
│  │    Parent: Block A                               │   │
│  │    [Edit] [Delete]                               │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │ 🌳 Yard                                          │   │
│  │    Building: Outdoor | Floor: 0 | Capacity: 100 │   │
│  │    [Edit] [Delete]                               │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Components
- **LocationCard** - Shows location with icon based on type
- **FilterBar** - Filter by type and building

### Backend Endpoints
- `GET /api/v1/locations` - List all locations
- `DELETE /api/v1/locations/{id}` - Delete location

---

## Screen 6: Create Roll Call

**Route:** `/rollcalls/new`

**Purpose:** Create new roll call with route

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Create Roll Call                          [← Back]     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │  Roll Call Details                              │   │
│  │                                                  │   │
│  │  Name *                                          │   │
│  │  [Morning Roll Call - Jan 28]                   │   │
│  │                                                  │   │
│  │  Scheduled Time *                                │   │
│  │  [2026-01-28T09:00]                              │   │
│  │                                                  │   │
│  │  Officer ID                                      │   │
│  │  [OFFICER001]                                    │   │
│  │                                                  │   │
│  │  Notes                                           │   │
│  │  [_________________________________]             │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Route (Ordered Locations)                      │   │
│  │                                                  │   │
│  │  Available Locations:                           │   │
│  │  ┌─────────────────────────────────────────┐    │   │
│  │  │ □ Block A (0 prisoners)                 │    │   │
│  │  │ □ Cell A-101 (John Doe)                 │    │   │
│  │  │ □ Cell A-102 (Jane Smith)               │    │   │
│  │  │ □ Cell B-201 (Mike Johnson)             │    │   │
│  │  │ □ Yard (0 prisoners)                    │    │   │
│  │  └─────────────────────────────────────────┘    │   │
│  │                                                  │   │
│  │  Selected Route:                                │   │
│  │  ┌─────────────────────────────────────────┐    │   │
│  │  │ 1. Cell A-101 (1 prisoner) [↑] [↓] [×] │    │   │
│  │  │ 2. Cell A-102 (1 prisoner) [↑] [↓] [×] │    │   │
│  │  │ 3. Cell B-201 (1 prisoner) [↑] [↓] [×] │    │   │
│  │  └─────────────────────────────────────────┘    │   │
│  │                                                  │   │
│  │  [Cancel]                  [Create Roll Call]   │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

### Features
- Drag-and-drop or up/down arrows to reorder route
- Auto-populate expected prisoners based on cell assignments
- Validation: at least one location required

### Backend Endpoints
- `GET /api/v1/locations` - Get available locations
- `GET /api/v1/inmates` - Get prisoners for location assignment
- `POST /api/v1/rollcalls` - Create roll call

---

## Screen 7: Active Roll Call

**Route:** `/rollcalls/[id]/active`

**Purpose:** Conduct roll call with webcam verification

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Morning Roll Call                         [End Early]  │
│  Progress: 2/3 locations ████████░░                     │
├─────────────────────────────────────────────────────────┤
│  Current Location: Cell A-102                           │
│  Expected: Jane Smith (#A12346)                         │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────┐   │
│  │         ┌─────────────────────────┐             │   │
│  │         │                         │             │   │
│  │         │   [WEBCAM LIVE VIEW]    │             │   │
│  │         │                         │             │   │
│  │         │   [Scanning overlay]    │             │   │
│  │         │                         │             │   │
│  │         └─────────────────────────┘             │   │
│  │                                                  │   │
│  │  Status: 🔍 Scanning for face...                │   │
│  │                                                  │   │
│  │  ┌─────────────────────────────────────────┐    │   │
│  │  │ ✓ Match Found!                          │    │   │
│  │  │ Jane Smith (#A12346)                    │    │   │
│  │  │ Confidence: 89%                         │    │   │
│  │  │ Recommendation: Confirm                 │    │   │
│  │  │                                         │    │   │
│  │  │ [✓ Confirm] [↻ Retry] [Manual Override]│    │   │
│  │  └─────────────────────────────────────────┘    │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Route Progress:                                        │
│  ✓ Cell A-101 (John Doe verified)                      │
│  → Cell A-102 (Current)                                │
│  ○ Cell B-201 (Pending)                                │
│                                                         │
│  [← Previous Location]        [Next Location →]        │
└─────────────────────────────────────────────────────────┘
```

### States
1. **Scanning** - Webcam active, sending frames to server
2. **Match Found** - Prisoner identified, awaiting confirmation
3. **Confirmed** - Verification recorded, ready for next
4. **Manual Override** - Officer manually verifies
5. **Error** - Network/detection error

### Backend Endpoints
- `POST /api/v1/verify/quick` - Verify face (multipart/form-data)
- `POST /api/v1/rollcalls/{id}/verification` - Record verification
- `POST /api/v1/rollcalls/{id}/complete` - Complete roll call

### Verification Loop
```javascript
let isScanning = true;
let lastScanTime = 0;
const SCAN_INTERVAL = 500;

async function verificationLoop(videoElement, locationId, rollCallId) {
  if (!isScanning) return;
  
  const now = Date.now();
  if (now - lastScanTime < SCAN_INTERVAL) {
    requestAnimationFrame(() => verificationLoop(videoElement, locationId, rollCallId));
    return;
  }
  
  lastScanTime = now;
  const frame = captureFrame(videoElement);
  
  try {
    const result = await verifyFrame(frame, locationId, rollCallId);
    updateVerificationUI(result);
    
    if (result.matched && result.confidence >= 0.75) {
      isScanning = false;
      showConfirmation(result);
    }
  } catch (error) {
    console.error('Verification error:', error);
    // Continue scanning
  }
  
  requestAnimationFrame(() => verificationLoop(videoElement, locationId, rollCallId));
}
```

---

## Screen 8: Roll Call Report

**Route:** `/rollcalls/[id]`

**Purpose:** View detailed roll call results

### Layout

```
┌─────────────────────────────────────────────────────────┐
│  Morning Roll Call - Jan 28, 2026          [← Back]     │
│  Status: Completed ✓                                    │
│  Started: 9:00 AM | Completed: 9:15 AM | Duration: 15m  │
├─────────────────────────────────────────────────────────┤
│  Summary                                                │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Total Locations: 3                             │   │
│  │  Total Prisoners: 3                             │   │
│  │  Verified: 3 ✓ | Not Found: 0 | Manual: 0      │   │
│  │  Average Confidence: 87%                        │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  Detailed Results                                       │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Location: Cell A-101                           │   │
│  │  Arrived: 9:02 AM | Completed: 9:05 AM          │   │
│  │                                                  │   │
│  │  ✓ John Doe (#A12345)                           │   │
│  │     Confidence: 91% | Time: 9:03 AM             │   │
│  │     Status: Verified                            │   │
│  │     [View Photo]                                │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Location: Cell A-102                           │   │
│  │  Arrived: 9:06 AM | Completed: 9:10 AM          │   │
│  │                                                  │   │
│  │  ✓ Jane Smith (#A12346)                         │   │
│  │     Confidence: 89% | Time: 9:08 AM             │   │
│  │     Status: Verified                            │   │
│  │     [View Photo]                                │   │
│  └─────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────┐   │
│  │  Location: Cell B-201                           │   │
│  │  Arrived: 9:11 AM | Completed: 9:14 AM          │   │
│  │                                                  │   │
│  │  ✓ Mike Johnson (#A12347)                       │   │
│  │     Confidence: 82% | Time: 9:12 AM             │   │
│  │     Status: Verified                            │   │
│  │     [View Photo]                                │   │
│  └─────────────────────────────────────────────────┘   │
│                                                         │
│  [Export PDF] [Export CSV]                              │
└─────────────────────────────────────────────────────────┘
```

### Backend Endpoints
- `GET /api/v1/rollcalls/{id}` - Get roll call details
- `GET /api/v1/rollcalls/{id}/verifications` - Get verification records (if separate endpoint exists)

---

## Responsive Design

All screens use Tailwind's responsive utilities:

```html
<!-- Mobile-first approach -->
<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  <!-- Cards adapt to screen size -->
</div>

<!-- Navigation collapses on mobile -->
<nav class="hidden md:flex space-x-4">
  <!-- Desktop nav -->
</nav>
<button class="md:hidden">
  <!-- Mobile menu button -->
</button>
```

**Breakpoints:**
- `sm`: 640px (tablets)
- `md`: 768px (small laptops)
- `lg`: 1024px (desktops)
- `xl`: 1280px (large screens)

---

*Next document: `web-ui-api-mapping.md` for complete endpoint integration details*
