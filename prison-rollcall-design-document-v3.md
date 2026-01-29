# Prison Roll Call

## Technical Design Document — MVP

**Version 3.0 | January 2025**

---

## Executive Summary

Prison Roll Call is a mobile application designed to streamline inmate verification during facility roll calls. The app enables officers to plan efficient routes through the facility, scan inmate faces for identification, and verify inmates are in their assigned locations.

**Architecture:** The mobile app handles UI, camera capture, and workflow state. All ML inference (face detection, embedding extraction, matching) runs on a **tethered laptop server** acting as a local WiFi hotspot. This "brain" runs a FastAPI server, keeping the mobile app lightweight and enabling use of powerful models without device constraints.

This document specifies the **MVP-Core** architecture with clean separation between the mobile client and ML server, enabling parallel development by independent teams.

---

## Non-Goals (Explicit Exclusions)

The following are explicitly **out of scope** for MVP:

- **No cloud sync** — all data remains on local network (device + server)
- **No internet connectivity required** — closed local network only
- **No multi-device reconciliation** — single mobile device per roll call
- **No identity management / SSO** — officer auth is stubbed
- **No legal evidence guarantees** — photos are operational, not evidentiary
- **No model retraining** — inference only, no learning
- **No cross-roll-call behavioural tracking** — each roll call is isolated
- **No integration with prison management systems** — standalone operation

---

## System Architecture

### High-Level Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        PRISON FACILITY                          │
│                                                                 │
│   ┌─────────────┐         WiFi Hotspot        ┌─────────────┐  │
│   │             │        (No Internet)        │             │  │
│   │   Mobile    │◄──────────────────────────► │   Laptop    │  │
│   │   Device    │         HTTP/REST           │   Server    │  │
│   │             │                             │   (Brain)   │  │
│   │  - UI       │                             │             │  │
│   │  - Camera   │                             │  - FastAPI  │  │
│   │  - Workflow │                             │  - ML Model │  │
│   │  - SQLite   │                             │  - Embeddings│ │
│   │             │                             │  - SQLite   │  │
│   └─────────────┘                             └─────────────┘  │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibilities |
|-----------|------------------|
| **Mobile App** | UI/UX, camera capture, image compression, workflow state, roll call progress, offline queue, local caching |
| **ML Server** | Face detection, embedding extraction, face matching, embedding storage, inmate database (source of truth) |

### Network Topology

- Laptop runs as WiFi hotspot (no internet uplink)
- Mobile device connects to laptop's hotspot
- Server runs on `http://192.168.x.1:8000` (configurable)
- All traffic is local — no data leaves the facility network

### Why Tethered Architecture?

| Benefit | Description |
|---------|-------------|
| **Model flexibility** | Run full ArcFace/AdaFace models without mobile constraints |
| **No device limits** | Works on any Android device with camera |
| **Easy updates** | Update models on laptop without app store deployment |
| **Better accuracy** | GPU inference on laptop outperforms mobile NPU |
| **Simpler app** | Mobile app is thin client — faster development |
| **Debugging** | Full access to server logs, model outputs, embeddings |

---

## Technology Stack

### Mobile App (React Native)

- React Native 0.73+ with TypeScript
- React Navigation for routing
- Zustand for state management
- SQLite (expo-sqlite) for local cache/queue
- react-native-vision-camera for camera
- Axios for HTTP client
- Jest + React Native Testing Library

### ML Server (Python/FastAPI)

- Python 3.11+
- FastAPI + Uvicorn
- **DeepFace 0.0.93+** for face recognition (unified interface)
  - Detection: RetinaFace (accuracy-first)
  - Recognition: Facenet512 or ArcFace (switchable)
  - GPU-accelerated with TensorFlow/Keras
- OpenCV for image processing
- SQLite for embeddings database
- NumPy for vector operations
- Pydantic for validation
- Pytest for testing

---

## Performance Budget

### Mobile App

| Operation | Target | Acceptable |
|-----------|--------|------------|
| Camera preview | 30fps | 24fps |
| Image capture + compress | <200ms | <400ms |
| Screen transition | <100ms | <200ms |
| Local DB query | <50ms | <100ms |

### ML Server

| Operation | Target | Acceptable | Hardware |
|-----------|--------|------------|----------|
| Face detection | <100ms | <200ms | CPU |
| Face detection | <30ms | <50ms | GPU |
| Embedding extraction | <150ms | <300ms | CPU |
| Embedding extraction | <50ms | <100ms | GPU |
| 1:N matching (1000) | <20ms | <50ms | CPU |
| Full verify pipeline | <300ms | <500ms | CPU |
| Full verify pipeline | <100ms | <200ms | GPU |

### Network

| Metric | Target | Acceptable |
|--------|--------|------------|
| Image upload (compressed) | <500ms | <1s |
| API round-trip (no image) | <50ms | <100ms |
| Reconnection time | <2s | <5s |

**Minimum Server Spec:** i5/Ryzen 5, 16GB RAM, optional NVIDIA GPU (RTX 3060+)

**Minimum Mobile Spec:** Android 10+, 4GB RAM, camera with autofocus

---

## Security & Compliance

### Network Security

| Layer | Protection |
|-------|------------|
| WiFi | WPA3 with strong password (facility-managed) |
| Transport | HTTPS with self-signed cert (optional for MVP) |
| API Auth | API key in header (rotated per shift) |

### Data Protection

| Data Type | Mobile (Cache) | Server (Source) | Retention |
|-----------|----------------|-----------------|-----------|
| Inmate photos | Compressed, temporary | AES-256 encrypted | Until unenrolled |
| Face embeddings | Not stored | AES-256 encrypted | Until unenrolled |
| Verification photos | Not stored | AES-256 encrypted | 30 days |
| Roll call records | Local cache | Source of truth | 90 days |

### Device Loss Protocol

**Mobile device lost:**
- No embeddings on device — minimal exposure
- Local cache contains only workflow state
- Server remains secure
- Re-pair new device to server

**Server laptop lost:**
- Full database exposure risk
- Encrypted SQLite mitigates (requires password)
- MDM remote wipe recommended
- Re-enroll all inmates required (worst case)

### Embedding Reversibility Statement

Face embeddings are 512-dimensional vectors derived via one-way transformation. They cannot be used to reconstruct the original face image.

### Regulatory Assumptions

- Face recognition limited to **enrolled inmates only**
- No speculative matching against external databases
- No model fine-tuning on inmate data
- Facility responsible for consent/notification per local law
- System does not make detention decisions — officer has final authority

---

## Face Recognition Policy

### Confidence Thresholds

Thresholds are facility-configurable via server config:

```python
class FaceRecognitionPolicy(BaseModel):
    # Verification (during roll call)
    verification_threshold: float = 0.75
    
    # Enrollment (capturing reference photo)
    enrollment_quality_threshold: float = 0.80
    
    # Auto-accept (no officer confirmation needed)
    auto_accept_threshold: float = 0.92
    
    # Force manual review (low confidence)
    manual_review_threshold: float = 0.60
    
    # Environmental adjustments
    low_light_adjustment: float = -0.05
    
    # Facility identifier
    facility_id: str = "default"
```

### Threshold Behaviour

| Confidence | Behaviour | Officer Action |
|------------|-----------|----------------|
| ≥0.92 | Auto-accept | Review if desired |
| 0.75–0.91 | Suggest match | Confirm or reject |
| 0.60–0.74 | Low confidence | Manual verification required |
| <0.60 | No match | Must use manual override |

---

## Failure Modes & Degraded Operation

### Network Failures

| Failure | Detection | User Feedback | Fallback |
|---------|-----------|---------------|----------|
| Server unreachable | Connection timeout | "Cannot connect to server" | Queue mode (see below) |
| WiFi disconnected | Network state change | "WiFi disconnected — reconnecting" | Auto-reconnect loop |
| Slow response | Timeout >2s | "Server slow — retrying" | Retry with backoff |
| Server crash | 5xx errors | "Server error — contact admin" | Queue mode |

### Queue Mode (Offline Fallback)

When server is unreachable, mobile app enters **Queue Mode**:

1. Photos captured and stored locally (compressed)
2. Roll call workflow continues with "pending verification" status
3. Verification requests queued with timestamps
4. When connection restored, queue syncs automatically
5. Officer notified of sync results

**Queue limits:** 50 photos max, 500MB storage, 4-hour expiry

### Camera Failures

| Failure | Detection | User Feedback | Fallback |
|---------|-----------|---------------|----------|
| Camera unavailable | Permission/hardware error | "Camera not available" | Manual mode |
| Low light | Server quality response | "Lighting too low" | Flash or manual |
| Camera frozen | No frames 3s | "Camera paused — tap to retry" | Restart session |

### Detection Failures (Server-Side)

| Failure | Server Response | User Feedback | Fallback |
|---------|-----------------|---------------|----------|
| No face detected | `detected: false` | "No face detected" | Retry or manual |
| Multiple faces | `face_count > 1` | "Multiple faces — isolate inmate" | Retry |
| Quality too low | `quality < threshold` | "Image quality too low" | Improve conditions |
| Model not loaded | 503 Service Unavailable | "Server initializing" | Wait and retry |

### Verification Failures

| Failure | Detection | User Feedback | Fallback |
|---------|-----------|---------------|----------|
| No match found | `confidence < threshold` | "No match — verify manually" | Manual override |
| Wrong location | Match but wrong location | "Inmate assigned elsewhere" | Log discrepancy |
| Not enrolled | No embedding on file | "Not enrolled — enroll now?" | Enroll in-flow |

---

## Human Factors Considerations

### Designed for Operational Reality

**Fatigue mitigation:**
- Large touch targets (minimum 48dp)
- High contrast UI
- Clear audio/haptic feedback on verification
- Progress always visible
- Server status always visible

**Over-trust prevention:**
- No "auto-complete" of roll calls
- Confidence score always visible (not just green tick)
- Periodic "attention check" prompts on long roll calls (Post-MVP)

**Network awareness:**
- Clear connection status indicator
- Queue count when offline
- Sync progress when reconnecting

### Manual Override Guidance

Manual override is **expected and legitimate** when:
- Inmate has injury/bandaging affecting face
- Lighting genuinely cannot be improved
- Network unavailable and queue full
- New inmate not yet enrolled

Manual override is **discouraged** (flagged for review) when:
- Used >3 times per roll call
- Used repeatedly for same inmate
- No notes provided
- Server was available but bypassed

---

## API Specification

### Base Configuration

```
Base URL: http://{SERVER_IP}:8000/api/v1
Content-Type: application/json (except image uploads: multipart/form-data)
Auth: X-API-Key header
```

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Server health check |
| GET | `/policy` | Get current recognition policy |
| **Inmates** | | |
| GET | `/inmates` | List all inmates |
| GET | `/inmates/{id}` | Get inmate by ID |
| POST | `/inmates` | Create inmate |
| PUT | `/inmates/{id}` | Update inmate |
| DELETE | `/inmates/{id}` | Delete inmate |
| GET | `/inmates/location/{location_id}` | Get inmates by location |
| GET | `/inmates/block/{block}` | Get inmates by block |
| **Enrollment** | | |
| POST | `/enrollment/{inmate_id}` | Enroll face (multipart) |
| DELETE | `/enrollment/{inmate_id}` | Unenroll face |
| GET | `/enrollment/status` | Get enrollment stats |
| **Verification** | | |
| POST | `/verify` | Verify face against candidates (multipart) |
| POST | `/verify/quick` | Quick verify at location (multipart) |
| POST | `/detect` | Detect face only (multipart) |
| **Locations** | | |
| GET | `/locations` | List all locations |
| POST | `/locations` | Create location |
| PUT | `/locations/{id}` | Update location |
| DELETE | `/locations/{id}` | Delete location |
| **Roll Calls** | | |
| GET | `/rollcalls` | List roll calls |
| POST | `/rollcalls` | Create roll call |
| GET | `/rollcalls/{id}` | Get roll call detail |
| POST | `/rollcalls/{id}/start` | Start roll call |
| POST | `/rollcalls/{id}/complete` | Complete roll call |
| POST | `/rollcalls/{id}/cancel` | Cancel roll call |
| POST | `/rollcalls/{id}/verification` | Record verification |
| **Sync** | | |
| POST | `/sync/queue` | Upload queued verifications |
| **Schedules** | | |
| GET | `/schedules` | List schedule entries (paginated) |
| GET | `/schedules/inmate/{id}` | Get prisoner's schedule |
| GET | `/schedules/location/{id}` | Who's scheduled at location |
| GET | `/schedules/now` | Current expected locations |
| GET | `/schedules/at` | Expected locations at time |
| POST | `/schedules` | Create schedule entry |
| PUT | `/schedules/{id}` | Update schedule entry |
| DELETE | `/schedules/{id}` | Delete schedule entry |
| POST | `/schedules/sync` | Bulk import from external system |
| POST | `/rollcalls/generate` | Auto-generate from schedules (multi-location) |
| GET | `/rollcalls/expected/{id}` | Get expected prisoners at location |

---

## API Contracts (Detailed)

### Health Check

```
GET /health

Response 200:
{
  "status": "healthy",
  "model_loaded": true,
  "model_version": "arcface_r100",
  "enrolled_count": 342,
  "uptime_seconds": 3600
}
```

### Face Detection

```
POST /detect
Content-Type: multipart/form-data

Body:
  - image: File (JPEG, max 2MB)

Response 200:
{
  "detected": true,
  "face_count": 1,
  "bounding_box": {
    "x": 100,
    "y": 80,
    "width": 200,
    "height": 240
  },
  "landmarks": {
    "left_eye": [150, 120],
    "right_eye": [250, 120],
    "nose": [200, 180],
    "left_mouth": [160, 220],
    "right_mouth": [240, 220]
  },
  "quality": 0.87,
  "quality_issues": []
}

Response 200 (no face):
{
  "detected": false,
  "face_count": 0,
  "bounding_box": null,
  "landmarks": null,
  "quality": 0.0,
  "quality_issues": ["no_face"]
}
```

### Enrollment

```
POST /enrollment/{inmate_id}
Content-Type: multipart/form-data

Body:
  - image: File (JPEG, max 2MB)

Response 200:
{
  "success": true,
  "inmate_id": "abc123",
  "quality": 0.89,
  "enrolled_at": "2025-01-05T14:30:00Z",
  "embedding_version": "arcface_r100"
}

Response 400:
{
  "success": false,
  "error": "quality_too_low",
  "quality": 0.45,
  "quality_issues": ["blur", "low_light"],
  "message": "Image quality below threshold (0.80)"
}

Response 404:
{
  "error": "inmate_not_found",
  "message": "Inmate abc123 does not exist"
}
```

### Verification

```
POST /verify/quick
Content-Type: multipart/form-data

Body:
  - image: File (JPEG, max 2MB)
  - location_id: string
  - roll_call_id: string

Response 200 (match found):
{
  "matched": true,
  "inmate_id": "abc123",
  "inmate": {
    "id": "abc123",
    "inmate_number": "A12345",
    "first_name": "John",
    "last_name": "Doe",
    "cell_block": "A",
    "cell_number": "101"
  },
  "confidence": 0.89,
  "threshold_used": 0.75,
  "recommendation": "confirm",
  "at_expected_location": true,
  "all_matches": [
    {"inmate_id": "abc123", "confidence": 0.89},
    {"inmate_id": "def456", "confidence": 0.34}
  ],
  "detection": {
    "quality": 0.85,
    "quality_issues": []
  }
}

Response 200 (no match):
{
  "matched": false,
  "inmate_id": null,
  "inmate": null,
  "confidence": 0.42,
  "threshold_used": 0.75,
  "recommendation": "no_match",
  "at_expected_location": null,
  "all_matches": [
    {"inmate_id": "xyz789", "confidence": 0.42}
  ],
  "detection": {
    "quality": 0.78,
    "quality_issues": []
  }
}
```

### Record Verification

```
POST /rollcalls/{id}/verification

Body:
{
  "inmate_id": "abc123",
  "location_id": "loc456",
  "status": "verified",
  "confidence": 0.89,
  "is_manual_override": false,
  "manual_override_reason": null,
  "notes": "",
  "photo_data": "base64..." // optional, for audit
}

Response 201:
{
  "id": "ver789",
  "roll_call_id": "rc123",
  "inmate_id": "abc123",
  "location_id": "loc456",
  "status": "verified",
  "confidence": 0.89,
  "timestamp": "2025-01-05T14:35:00Z",
  "is_manual_override": false
}
```

### Queue Sync

```
POST /sync/queue

Body:
{
  "roll_call_id": "rc123",
  "items": [
    {
      "local_id": "queue001",
      "queued_at": "2025-01-05T14:20:00Z",
      "location_id": "loc456",
      "image_data": "base64..."
    },
    {
      "local_id": "queue002",
      "queued_at": "2025-01-05T14:21:00Z",
      "location_id": "loc456",
      "image_data": "base64..."
    }
  ]
}

Response 200:
{
  "processed": 2,
  "results": [
    {
      "local_id": "queue001",
      "success": true,
      "verification": {
        "matched": true,
        "inmate_id": "abc123",
        "confidence": 0.87,
        "status": "verified"
      }
    },
    {
      "local_id": "queue002",
      "success": true,
      "verification": {
        "matched": false,
        "inmate_id": null,
        "confidence": 0.32,
        "status": "not_found"
      }
    }
  ]
}
```

### Auto-Generate Roll Call

```
POST /rollcalls/generate

Body:
{
  "location_ids": ["loc123", "loc456"],  // One or more location IDs
  "scheduled_at": "2025-01-05T14:00:00Z",
  "include_empty": true,                 // Include empty cells in route
  "name": "Morning Roll Call A Wing",    // Optional
  "officer_id": "officer-001"            // Officer conducting roll call
}

Response 200:
{
  "location_ids": ["loc123", "loc456"],
  "location_names": ["A Wing", "B Wing"],
  "scheduled_at": "2025-01-05T14:00:00Z",
  "route": [
    {
      "order": 0,
      "location_id": "cell001",
      "location_name": "A1-01",
      "location_type": "cell",
      "building": "Block 1",
      "floor": 0,
      "is_occupied": true,
      "expected_count": 2,
      "walking_distance_meters": 0,
      "walking_time_seconds": 0
    },
    {
      "order": 1,
      "location_id": "cell002",
      "location_name": "A1-02",
      "location_type": "cell",
      "building": "Block 1",
      "floor": 0,
      "is_occupied": true,
      "expected_count": 1,
      "walking_distance_meters": 5,
      "walking_time_seconds": 8
    }
  ],
  "summary": {
    "total_locations": 47,
    "occupied_locations": 42,
    "empty_locations": 5,
    "total_prisoners_expected": 78,
    "estimated_time_seconds": 2940  // Walking + 30s per prisoner
  }
}

Response 400 (empty list):
{
  "detail": "At least one location ID required"
}

Response 404 (invalid location):
{
  "detail": "Location abc123 not found"
}

Response 400 (no cells):
{
  "detail": "No cells found in specified locations"
}
```

**Multi-Location Support:**

The endpoint accepts multiple location IDs for flexible roll call generation:

- **Single location**: `["houseblock-1"]` - all cells in houseblock
- **Multiple wings**: `["a-wing", "b-wing"]` - combine two wings
- **Two landings**: `["a1-landing", "a2-landing"]` - just specific landings
- **Specific cells**: `["cell-101", "cell-205", "cell-310"]` - arbitrary selection
- **Mixed hierarchy**: `["b-wing", "a1-landing", "cell-405"]` - combine levels

The service automatically:
- Collects all cells from parent locations (wings, landings, houseblocks)
- Adds individual cells directly
- Deduplicates overlapping selections (e.g., wing + one of its cells)
- Calculates optimal route through all cells
- Counts expected prisoners based on schedules at the specified time

### Expected Prisoners at Location

```
GET /rollcalls/expected/{location_id}?at_time=2025-01-05T14:00:00Z

Response 200:
{
  "location_id": "cell001",
  "total_expected": 2,
  "expected_prisoners": [
    {
      "inmate_id": "inmate123",
      "inmate_number": "A12345",
      "first_name": "John",
      "last_name": "Doe",
      "is_enrolled": true,
      "home_cell_id": "cell001",
      "is_at_home_cell": true,
      "current_activity": "lock_up",
      "next_appointment": {
        "activity_type": "healthcare",
        "location_name": "Healthcare Unit",
        "start_time": "14:30",
        "minutes_until": 30,
        "is_urgent": false
      },
      "priority_score": 70
    },
    {
      "inmate_id": "inmate456",
      "inmate_number": "A12346",
      "first_name": "Jane",
      "last_name": "Smith",
      "is_enrolled": true,
      "home_cell_id": "cell001",
      "is_at_home_cell": true,
      "current_activity": "lock_up",
      "next_appointment": {
        "activity_type": "visits",
        "location_name": "Visits Hall",
        "start_time": "14:10",
        "minutes_until": 10,
        "is_urgent": true
      },
      "priority_score": 105  // Higher priority - verify first
    }
  ]
}
```

**Priority Scoring:**

Prisoners are sorted by priority score (highest first):
- Base score: 50
- +50 if appointment < 15 minutes
- +40 if appointment < 30 minutes
- +20 if appointment < 60 minutes
- +10 for healthcare appointments
- +5 for visits (family)
- Maximum score: 100

This allows officers to prioritize verifying prisoners with imminent appointments first.

---

## Data Models

### Server-Side (Python/Pydantic)

#### Inmate

```python
class Inmate(BaseModel):
    id: str  # UUID
    inmate_number: str  # Facility ID, e.g., "A12345"
    first_name: str
    last_name: str
    date_of_birth: date
    cell_block: str
    cell_number: str
    photo_uri: str | None = None
    is_enrolled: bool = False
    enrolled_at: datetime | None = None
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class InmateCreate(BaseModel):
    inmate_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    cell_block: str
    cell_number: str

class InmateUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    cell_block: str | None = None
    cell_number: str | None = None
    is_active: bool | None = None
```

#### Location

```python
class LocationType(str, Enum):
    BLOCK = "block"
    CELL = "cell"
    COMMON_AREA = "common_area"
    YARD = "yard"
    MEDICAL = "medical"
    ADMIN = "admin"

class Location(BaseModel):
    id: str
    name: str
    type: LocationType
    parent_id: str | None = None
    capacity: int = 1
    floor: int = 0
    building: str
```

#### RollCall

```python
class RollCallStatus(str, Enum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class RouteStop(BaseModel):
    id: str
    location_id: str
    order: int
    expected_inmates: list[str]  # Inmate IDs
    status: Literal["pending", "current", "completed", "skipped"] = "pending"
    arrived_at: datetime | None = None
    completed_at: datetime | None = None
    skip_reason: str | None = None

class RollCall(BaseModel):
    id: str
    name: str
    status: RollCallStatus
    scheduled_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    cancelled_reason: str | None = None
    route: list[RouteStop]
    officer_id: str
    notes: str = ""
```

#### Verification

```python
class VerificationStatus(str, Enum):
    VERIFIED = "verified"
    NOT_FOUND = "not_found"
    WRONG_LOCATION = "wrong_location"
    MANUAL = "manual"
    PENDING = "pending"  # For queued items

class ManualOverrideReason(str, Enum):
    FACIAL_INJURY = "facial_injury"
    LIGHTING_CONDITIONS = "lighting_conditions"
    TECHNICAL_FAILURE = "technical_failure"
    NOT_ENROLLED = "not_enrolled"
    NETWORK_UNAVAILABLE = "network_unavailable"
    OTHER = "other"

class Verification(BaseModel):
    id: str
    roll_call_id: str
    inmate_id: str
    location_id: str
    status: VerificationStatus
    confidence: float
    photo_uri: str | None = None
    timestamp: datetime
    is_manual_override: bool = False
    manual_override_reason: ManualOverrideReason | None = None
    notes: str = ""
```

#### Schedule

```python
class ActivityType(str, Enum):
    """Types of scheduled activities."""
    ROLL_CHECK = "roll_check"
    LOCK_UP = "lock_up"
    UNLOCK = "unlock"
    MEAL = "meal"
    WORK = "work"
    EDUCATION = "education"
    EXERCISE = "exercise"
    ASSOCIATION = "association"
    GYM = "gym"
    VISITS = "visits"
    HEALTHCARE = "healthcare"
    CHAPEL = "chapel"
    PROGRAMMES = "programmes"

class ScheduleEntry(BaseModel):
    """A scheduled activity for an inmate."""
    id: str
    inmate_id: str
    location_id: str
    day_of_week: int  # 0=Monday, 6=Sunday
    start_time: str  # "HH:MM"
    end_time: str  # "HH:MM"
    activity_type: ActivityType
    is_recurring: bool = True
    effective_date: date | None = None  # For one-off appointments
    source: str = "manual"  # "manual", "sync", "generated"
    source_id: str | None = None  # External system ID
    created_at: datetime
    updated_at: datetime

class ScheduleEntryCreate(BaseModel):
    """Data for creating a schedule entry."""
    inmate_id: str
    location_id: str
    day_of_week: int
    start_time: str
    end_time: str
    activity_type: ActivityType
    is_recurring: bool = True
    effective_date: date | None = None

class ScheduleEntryUpdate(BaseModel):
    """Data for updating a schedule entry."""
    location_id: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    activity_type: ActivityType | None = None
```

#### Face Recognition

```python
class BoundingBox(BaseModel):
    x: int
    y: int
    width: int
    height: int

class FaceLandmarks(BaseModel):
    left_eye: tuple[int, int]
    right_eye: tuple[int, int]
    nose: tuple[int, int]
    left_mouth: tuple[int, int]
    right_mouth: tuple[int, int]

class QualityIssue(str, Enum):
    NO_FACE = "no_face"
    MULTI_FACE = "multi_face"
    LOW_LIGHT = "low_light"
    BLUR = "blur"
    ANGLE = "angle"
    OCCLUSION = "occlusion"
    TOO_FAR = "too_far"
    TOO_CLOSE = "too_close"

class DetectionResult(BaseModel):
    detected: bool
    face_count: int
    bounding_box: BoundingBox | None
    landmarks: FaceLandmarks | None
    quality: float
    quality_issues: list[QualityIssue]

class MatchRecommendation(str, Enum):
    AUTO_ACCEPT = "auto_accept"
    CONFIRM = "confirm"
    REVIEW = "review"
    NO_MATCH = "no_match"

class MatchResult(BaseModel):
    matched: bool
    inmate_id: str | None
    inmate: Inmate | None
    confidence: float
    threshold_used: float
    recommendation: MatchRecommendation
    at_expected_location: bool | None
    all_matches: list[dict]  # [{inmate_id, confidence}]
    detection: DetectionResult
```

### Client-Side (TypeScript)

```typescript
// Types mirror server models — see src/types/index.ts

interface Inmate {
  id: string;
  inmateNumber: string;
  firstName: string;
  lastName: string;
  dateOfBirth: string;
  cellBlock: string;
  cellNumber: string;
  photoUri: string | null;
  isEnrolled: boolean;
  enrolledAt: string | null;
  isActive: boolean;
  createdAt: string;
  updatedAt: string;
}

interface VerifyResponse {
  matched: boolean;
  inmateId: string | null;
  inmate: Inmate | null;
  confidence: number;
  thresholdUsed: number;
  recommendation: 'auto_accept' | 'confirm' | 'review' | 'no_match';
  atExpectedLocation: boolean | null;
  allMatches: Array<{ inmateId: string; confidence: number }>;
  detection: DetectionResult;
}

// Queue item for offline mode
interface QueuedVerification {
  localId: string;
  queuedAt: string;
  rollCallId: string;
  locationId: string;
  imageData: string;  // base64
  status: 'pending' | 'syncing' | 'synced' | 'failed';
}
```

---

## Database Schema

### Server Database (SQLite)

```sql
-- Inmates
CREATE TABLE inmates (
    id TEXT PRIMARY KEY,
    inmate_number TEXT UNIQUE NOT NULL,
    first_name TEXT NOT NULL,
    last_name TEXT NOT NULL,
    date_of_birth TEXT NOT NULL,
    cell_block TEXT NOT NULL,
    cell_number TEXT NOT NULL,
    photo_uri TEXT,
    is_enrolled INTEGER DEFAULT 0,
    enrolled_at TEXT,
    is_active INTEGER DEFAULT 1,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_inmates_block ON inmates(cell_block);
CREATE INDEX idx_inmates_enrolled ON inmates(is_enrolled);
CREATE INDEX idx_inmates_number ON inmates(inmate_number);

-- Face embeddings (separate table for security)
CREATE TABLE embeddings (
    inmate_id TEXT PRIMARY KEY REFERENCES inmates(id),
    embedding BLOB NOT NULL,  -- 512 floats as bytes
    model_version TEXT NOT NULL,
    created_at TEXT NOT NULL
);

-- Locations
CREATE TABLE locations (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,
    parent_id TEXT REFERENCES locations(id),
    capacity INTEGER DEFAULT 1,
    floor INTEGER DEFAULT 0,
    building TEXT NOT NULL
);

CREATE INDEX idx_locations_type ON locations(type);
CREATE INDEX idx_locations_building ON locations(building);

-- Roll calls
CREATE TABLE roll_calls (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    status TEXT NOT NULL,
    scheduled_at TEXT NOT NULL,
    started_at TEXT,
    completed_at TEXT,
    cancelled_reason TEXT,
    route TEXT NOT NULL,  -- JSON
    officer_id TEXT NOT NULL,
    notes TEXT DEFAULT ''
);

CREATE INDEX idx_rollcalls_status ON roll_calls(status);
CREATE INDEX idx_rollcalls_scheduled ON roll_calls(scheduled_at);

-- Verifications
CREATE TABLE verifications (
    id TEXT PRIMARY KEY,
    roll_call_id TEXT NOT NULL REFERENCES roll_calls(id),
    inmate_id TEXT NOT NULL REFERENCES inmates(id),
    location_id TEXT NOT NULL REFERENCES locations(id),
    status TEXT NOT NULL,
    confidence REAL NOT NULL,
    photo_uri TEXT,
    timestamp TEXT NOT NULL,
    is_manual_override INTEGER DEFAULT 0,
    manual_override_reason TEXT,
    notes TEXT DEFAULT ''
);

CREATE INDEX idx_verifications_rollcall ON verifications(roll_call_id);
CREATE INDEX idx_verifications_inmate ON verifications(inmate_id);
CREATE INDEX idx_verifications_timestamp ON verifications(timestamp);

-- Audit log
CREATE TABLE audit_log (
    id TEXT PRIMARY KEY,
    timestamp TEXT NOT NULL,
    officer_id TEXT NOT NULL,
    action TEXT NOT NULL,
    entity_type TEXT NOT NULL,
    entity_id TEXT NOT NULL,
    details TEXT  -- JSON
);

CREATE INDEX idx_audit_timestamp ON audit_log(timestamp);
CREATE INDEX idx_audit_action ON audit_log(action);

-- Policy
CREATE TABLE policy (
    id TEXT PRIMARY KEY DEFAULT 'default',
    verification_threshold REAL DEFAULT 0.75,
    enrollment_quality_threshold REAL DEFAULT 0.80,
    auto_accept_threshold REAL DEFAULT 0.92,
    manual_review_threshold REAL DEFAULT 0.60,
    low_light_adjustment REAL DEFAULT -0.05,
    updated_at TEXT NOT NULL,
    updated_by TEXT NOT NULL
);

-- Schedule entries (prisoner timetables)
CREATE TABLE schedule_entries (
    id TEXT PRIMARY KEY,
    inmate_id TEXT NOT NULL REFERENCES inmates(id),
    location_id TEXT NOT NULL REFERENCES locations(id),
    day_of_week INTEGER NOT NULL,
    start_time TEXT NOT NULL,
    end_time TEXT NOT NULL,
    activity_type TEXT NOT NULL,
    is_recurring INTEGER DEFAULT 1,
    effective_date TEXT,
    source TEXT DEFAULT 'manual',
    source_id TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE INDEX idx_schedule_inmate ON schedule_entries(inmate_id);
CREATE INDEX idx_schedule_location ON schedule_entries(location_id);
CREATE INDEX idx_schedule_day_time ON schedule_entries(day_of_week, start_time);
CREATE INDEX idx_schedule_source ON schedule_entries(source, source_id);
```

### Mobile Cache Database (SQLite)

```sql
-- Cached inmates (for offline display)
CREATE TABLE cached_inmates (
    id TEXT PRIMARY KEY,
    data TEXT NOT NULL,  -- JSON
    cached_at TEXT NOT NULL
);

-- Verification queue (offline mode)
CREATE TABLE verification_queue (
    local_id TEXT PRIMARY KEY,
    roll_call_id TEXT NOT NULL,
    location_id TEXT NOT NULL,
    image_data TEXT NOT NULL,  -- base64
    queued_at TEXT NOT NULL,
    status TEXT DEFAULT 'pending',
    sync_result TEXT,  -- JSON, filled after sync
    synced_at TEXT
);

CREATE INDEX idx_queue_status ON verification_queue(status);

-- Active roll call state
CREATE TABLE active_rollcall (
    id TEXT PRIMARY KEY DEFAULT 'current',
    roll_call_id TEXT NOT NULL,
    data TEXT NOT NULL,  -- JSON
    current_stop_index INTEGER DEFAULT 0,
    updated_at TEXT NOT NULL
);

-- Connection state
CREATE TABLE connection_state (
    id TEXT PRIMARY KEY DEFAULT 'state',
    server_url TEXT NOT NULL,
    api_key TEXT NOT NULL,
    is_connected INTEGER DEFAULT 0,
    last_connected_at TEXT
);
```

---

## Module Structure

### Server (FastAPI)

```
server/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app, middleware, startup
│   ├── config.py               # Settings, policy defaults
│   ├── dependencies.py         # Dependency injection
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── routes/
│   │   │   ├── health.py
│   │   │   ├── inmates.py
│   │   │   ├── enrollment.py
│   │   │   ├── verification.py
│   │   │   ├── locations.py
│   │   │   ├── rollcalls.py
│   │   │   ├── schedules.py
│   │   │   └── sync.py
│   │   └── middleware/
│   │       └── auth.py
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── face_recognition.py # Detection, embedding, matching
│   │   ├── inmate_service.py
│   │   ├── location_service.py
│   │   ├── rollcall_service.py
│   │   ├── schedule_service.py
│   │   └── audit_service.py
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── inmate.py
│   │   ├── location.py
│   │   ├── rollcall.py
│   │   ├── verification.py
│   │   ├── schedule.py
│   │   └── face.py
│   │
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite connection
│   │   ├── repositories/
│   │   │   ├── inmate_repo.py
│   │   │   ├── embedding_repo.py
│   │   │   ├── location_repo.py
│   │   │   ├── rollcall_repo.py
│   │   │   ├── verification_repo.py
│   │   │   └── schedule_repo.py
│   │   └── migrations/
│   │       ├── 001_initial.sql
│   │       ├── 002_multiple_embeddings.sql
│   │       ├── 003_location_connections.sql
│   │       └── 004_schedule_entries.sql
│   │
│   └── ml/
│       ├── __init__.py
│       ├── face_detector.py    # Face detection wrapper
│       ├── face_embedder.py    # Embedding extraction
│       ├── face_matcher.py     # 1:N matching
│       └── models/             # Model files (.onnx)
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py             # Fixtures
│   ├── unit/
│   │   ├── test_face_recognition.py
│   │   ├── test_inmate_service.py
│   │   └── test_matching.py
│   ├── integration/
│   │   ├── test_enrollment_flow.py
│   │   ├── test_verification_flow.py
│   │   └── test_api_endpoints.py
│   └── fixtures/
│       ├── images/
│       └── embeddings.py
│
├── scripts/
│   ├── setup_hotspot.sh        # WiFi hotspot setup
│   ├── seed_data.py            # Test data seeding
│   ├── generate_schedules.py   # Generate realistic 2-week schedules
│   └── export_audit.py         # Audit log export
│
├── requirements.txt
├── pyproject.toml
└── README.md
```

### Mobile App (React Native)

```
mobile/
├── src/
│   ├── components/
│   │   ├── core/               # Button, Card, Input, Modal, etc.
│   │   └── domain/             # InmateCard, CameraView, RouteProgress, etc.
│   │
│   ├── screens/
│   │   ├── HomeScreen.tsx
│   │   ├── ActiveRollCallScreen.tsx
│   │   ├── EnrollmentScreen.tsx
│   │   ├── InmateListScreen.tsx
│   │   ├── InmateDetailScreen.tsx
│   │   ├── LocationListScreen.tsx
│   │   ├── SettingsScreen.tsx
│   │   └── ConnectionScreen.tsx  # Server pairing
│   │
│   ├── navigation/
│   │   └── RootNavigator.tsx
│   │
│   ├── services/
│   │   ├── api.ts              # Axios client, endpoints
│   │   ├── connection.ts       # Connection state, reconnection
│   │   └── queue.ts            # Offline queue management
│   │
│   ├── stores/
│   │   ├── connectionStore.ts
│   │   ├── inmateStore.ts
│   │   ├── rollCallStore.ts
│   │   ├── cameraStore.ts
│   │   └── queueStore.ts
│   │
│   ├── hooks/
│   │   ├── useConnection.ts
│   │   ├── useCamera.ts
│   │   └── useVerification.ts
│   │
│   ├── database/
│   │   ├── schema.ts
│   │   ├── cache.ts
│   │   └── queue.ts
│   │
│   ├── types/
│   │   └── index.ts
│   │
│   └── utils/
│       ├── image.ts            # Compression, base64
│       └── validation.ts
│
├── __tests__/
│   ├── unit/
│   ├── components/
│   ├── screens/
│   └── integration/
│
├── app.json
├── package.json
└── README.md
```

---

## Screen Specifications

### Navigation Structure

```
RootNavigator
├── ConnectionScreen (if not paired)
└── MainTabs
    ├── HomeStack
    │   ├── HomeScreen
    │   ├── RollCallDetailScreen
    │   └── ActiveRollCallScreen
    ├── InmatesStack
    │   ├── InmateListScreen
    │   ├── InmateDetailScreen
    │   └── EnrollmentScreen
    ├── LocationsStack
    │   └── LocationListScreen
    └── SettingsStack
        └── SettingsScreen
```

### Key Screens

#### ConnectionScreen

Initial pairing with server.

| Element | Description |
|---------|-------------|
| ServerInput | IP address / hostname input |
| APIKeyInput | API key input (or QR scan) |
| ConnectButton | Test connection and save |
| StatusIndicator | Connection test result |
| Instructions | Setup guide for officers |

#### HomeScreen

| Element | Description |
|---------|-------------|
| ConnectionBanner | Server status: connected/disconnected/queue mode |
| ActiveRollCallCard | Current roll call progress |
| QueueIndicator | Pending items count if offline |
| UpcomingList | Next 5 scheduled roll calls |
| QuickActions | Start Roll Call, Sync Queue |
| StatsCard | Today's stats |

#### ActiveRollCallScreen

| Element | Description |
|---------|-------------|
| ConnectionStatus | Small indicator: 🟢 Connected / 🟡 Queue Mode |
| RouteProgress | Visual progress bar |
| CurrentStopHeader | Location, expected count, verified count |
| CameraView | Live camera with detection overlay |
| QualityFeedback | Real-time feedback from server |
| VerificationResult | Match result with confidence |
| ActionButtons | Confirm, Manual Override, Skip, Next |
| QueueBadge | Shows "Will sync when connected" if offline |

#### EnrollmentScreen

| Element | Description |
|---------|-------------|
| InmateHeader | Name, number, enrollment status |
| CameraView | Camera with alignment guide |
| CaptureButton | Disabled until connected |
| PreviewModal | Captured photo preview |
| ProcessingOverlay | "Sending to server..." |
| ResultDisplay | Quality score, success/failure |

---

## Test Infrastructure

### Server Tests (Pytest)

```
tests/
├── conftest.py                 # Shared fixtures
├── unit/
│   ├── test_face_detector.py
│   ├── test_face_embedder.py
│   ├── test_face_matcher.py
│   ├── test_policy.py
│   └── test_services.py
├── integration/
│   ├── test_enrollment_api.py
│   ├── test_verification_api.py
│   ├── test_rollcall_api.py
│   └── test_sync_api.py
└── fixtures/
    ├── images/
    │   ├── face_good.jpg
    │   ├── face_blur.jpg
    │   ├── face_dark.jpg
    │   ├── no_face.jpg
    │   └── multi_face.jpg
    └── embeddings.py
```

#### Example Server Tests

```python
# tests/unit/test_face_matcher.py

class TestFaceMatcher:
    def test_match_above_threshold(self, matcher, enrolled_embeddings):
        query = enrolled_embeddings["inmate_001"]
        result = matcher.find_match(query, enrolled_embeddings)
        
        assert result.matched is True
        assert result.inmate_id == "inmate_001"
        assert result.confidence > 0.99
        assert result.recommendation == MatchRecommendation.AUTO_ACCEPT

    def test_no_match_below_threshold(self, matcher, enrolled_embeddings):
        query = generate_random_embedding()
        result = matcher.find_match(query, enrolled_embeddings)
        
        assert result.matched is False
        assert result.inmate_id is None
        assert result.recommendation == MatchRecommendation.NO_MATCH

    def test_low_confidence_requires_review(self, matcher, similar_embeddings):
        query = similar_embeddings["query"]
        result = matcher.find_match(query, similar_embeddings["candidates"])
        
        assert result.matched is False
        assert result.confidence > 0.60
        assert result.confidence < 0.75
        assert result.recommendation == MatchRecommendation.REVIEW


# tests/integration/test_verification_api.py

class TestVerificationAPI:
    async def test_quick_verify_success(self, client, enrolled_inmate, test_image):
        response = await client.post(
            "/api/v1/verify/quick",
            files={"image": test_image},
            data={
                "location_id": enrolled_inmate.location_id,
                "roll_call_id": "rc_001"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is True
        assert data["inmate_id"] == enrolled_inmate.id
        assert data["recommendation"] in ["auto_accept", "confirm"]

    async def test_verify_no_face(self, client, no_face_image):
        response = await client.post(
            "/api/v1/verify/quick",
            files={"image": no_face_image},
            data={"location_id": "loc_001", "roll_call_id": "rc_001"}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["matched"] is False
        assert data["detection"]["detected"] is False
        assert "no_face" in data["detection"]["quality_issues"]
```

### Mobile Tests (Jest)

```typescript
// __tests__/integration/queueMode.test.ts

describe('Queue Mode', () => {
  beforeEach(() => {
    mockConnection.setConnected(false);
  });

  it('should queue verification when offline', async () => {
    const { result } = renderHook(() => useVerification());
    
    await act(async () => {
      await result.current.verify('rollcall-1', 'loc-1', mockPhoto);
    });
    
    const queue = useQueueStore.getState().items;
    expect(queue).toHaveLength(1);
    expect(queue[0].status).toBe('pending');
  });

  it('should sync queue when connection restored', async () => {
    // Add items to queue
    useQueueStore.getState().addItem(mockQueueItem);
    
    // Restore connection
    mockConnection.setConnected(true);
    mockServer.onPost('/sync/queue').reply(200, mockSyncResponse);
    
    await act(async () => {
      await useQueueStore.getState().sync();
    });
    
    const queue = useQueueStore.getState().items;
    expect(queue[0].status).toBe('synced');
  });

  it('should show queue count on home screen', () => {
    useQueueStore.getState().addItem(mockQueueItem);
    useQueueStore.getState().addItem(mockQueueItem);
    
    const { getByText } = render(<HomeScreen />);
    
    expect(getByText('2 pending')).toBeTruthy();
  });
});
```

---

## Implementation Phases

### Phase 1: Server Foundation (Week 1)

- FastAPI project setup
- Database schema and migrations
- Basic CRUD endpoints (inmates, locations)
- Health check endpoint
- Pytest infrastructure

### Phase 2: ML Pipeline (Week 2)

- **Face detection integration (DeepFace)**
  - Wrapper classes around DeepFace library
  - RetinaFace detector for accuracy (GPU-accelerated)
  - Test fixtures from CelebA dataset (~20 diverse samples)
- **Embedding extraction**
  - Facenet512 model (98.4% accuracy benchmark)
  - Fallback to ArcFace (96.7% accuracy benchmark)
  - 512-dimensional normalized vectors
- **Matching algorithm with policy**
  - Cosine similarity with configurable thresholds
  - GPU-optimized for <100ms total pipeline
- **API Endpoints**
  - Detection endpoint
  - Enrollment endpoint
  - Verification endpoint

### Phase 3: Mobile Foundation (Week 3)

- React Native project setup
- Connection/pairing screen
- API client with error handling
- Connection state management
- Basic navigation

### Phase 4: Mobile Core Features (Week 4)

- Inmate list (from server)
- Camera integration
- Enrollment flow
- Verification flow
- Result display

### Phase 5: Roll Call Workflow (Week 5)

- Server: roll call CRUD, route stops
- Mobile: roll call creation
- Mobile: ActiveRollCallScreen
- Progress tracking
- Stop navigation

### Phase 6: Offline & Polish (Week 6)

- Queue mode implementation
- Sync endpoint and flow
- Connection recovery
- UI polish
- Error states

### Phase 7: Regime/Schedule System (Week 7)

- **Schedule data model**
  - Migration 004: schedule_entries table
  - Pydantic models for schedule entries
  - ActivityType enum
- **Schedule repository**
  - CRUD operations
  - Query by inmate, location, time
  - Bulk import for sync
- **Schedule service**
  - Business logic for schedule management
  - Conflict detection
  - Roll call generation from schedules
- **Schedule API endpoints**
  - List, create, update, delete schedules
  - Query endpoints (now, at time, by inmate/location)
  - Auto-generate roll calls
- **Demo data generator**
  - Generate 2 weeks of realistic schedules for 1600 prisoners
  - Include work assignments, education, healthcare appointments
  - Weekday vs weekend patterns
  - Individual variations (doctor appointments, legal visits)

### Phase 8: Hardening (Week 8)

- Full test coverage
- Performance optimization
- Security review
- Documentation
- Deployment scripts

---

## Deployment

### Server Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Download ML models
python scripts/download_models.py

# 3. Initialize database
python scripts/init_db.py

# 4. Set up WiFi hotspot (Linux)
sudo ./scripts/setup_hotspot.sh

# 5. Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Hotspot Configuration (Linux)

```bash
#!/bin/bash
# scripts/setup_hotspot.sh

SSID="PrisonRollCall"
PASSWORD="<secure-password>"

nmcli device wifi hotspot ifname wlan0 ssid "$SSID" password "$PASSWORD"
nmcli connection modify Hotspot ipv4.addresses 192.168.4.1/24
nmcli connection modify Hotspot ipv4.method shared
```

### Mobile Configuration

On first launch:
1. Connect to "PrisonRollCall" WiFi
2. Open app → Connection screen
3. Enter server IP: `192.168.4.1`
4. Enter API key (generated on server)
5. Test connection → Save

---

## Appendix

### A. Image Compression (Mobile)

```typescript
// src/utils/image.ts

import { manipulateAsync, SaveFormat } from 'expo-image-manipulator';

export async function compressForUpload(uri: string): Promise<string> {
  const result = await manipulateAsync(
    uri,
    [{ resize: { width: 640 } }],  // Max 640px width
    { compress: 0.8, format: SaveFormat.JPEG }
  );
  return result.uri;
}

export async function toBase64(uri: string): Promise<string> {
  const response = await fetch(uri);
  const blob = await response.blob();
  return new Promise((resolve) => {
    const reader = new FileReader();
    reader.onloadend = () => resolve(reader.result as string);
    reader.readAsDataURL(blob);
  });
}
```

### B. Embedding Storage (Server)

```python
# app/db/repositories/embedding_repo.py

import numpy as np
from typing import Optional

class EmbeddingRepository:
    def __init__(self, db):
        self.db = db
    
    def save(self, inmate_id: str, embedding: np.ndarray, model_version: str):
        blob = embedding.astype(np.float32).tobytes()
        self.db.execute(
            "INSERT OR REPLACE INTO embeddings VALUES (?, ?, ?, ?)",
            (inmate_id, blob, model_version, datetime.utcnow().isoformat())
        )
    
    def get(self, inmate_id: str) -> Optional[np.ndarray]:
        row = self.db.execute(
            "SELECT embedding FROM embeddings WHERE inmate_id = ?",
            (inmate_id,)
        ).fetchone()
        if row:
            return np.frombuffer(row[0], dtype=np.float32)
        return None
    
    def get_all(self) -> dict[str, np.ndarray]:
        rows = self.db.execute("SELECT inmate_id, embedding FROM embeddings").fetchall()
        return {row[0]: np.frombuffer(row[1], dtype=np.float32) for row in rows}
```

### C. Test Commands

```bash
# Server
pytest                              # All tests
pytest tests/unit                   # Unit only
pytest -k "enrollment"              # Pattern match
pytest --cov=app --cov-report=html  # Coverage

# Mobile
npm test                            # All tests
npm test -- --testPathPattern=queue # Queue tests
npm test -- --coverage              # Coverage
```

### D. Audit Log Actions

```python
class AuditAction(str, Enum):
    INMATE_CREATED = "inmate_created"
    INMATE_UPDATED = "inmate_updated"
    INMATE_DELETED = "inmate_deleted"
    FACE_ENROLLED = "face_enrolled"
    FACE_UNENROLLED = "face_unenrolled"
    ROLLCALL_STARTED = "rollcall_started"
    ROLLCALL_COMPLETED = "rollcall_completed"
    ROLLCALL_CANCELLED = "rollcall_cancelled"
    VERIFICATION_RECORDED = "verification_recorded"
    MANUAL_OVERRIDE_USED = "manual_override_used"
    STOP_SKIPPED = "stop_skipped"
    POLICY_UPDATED = "policy_updated"
    QUEUE_SYNCED = "queue_synced"
    CONNECTION_ESTABLISHED = "connection_established"
    CONNECTION_LOST = "connection_lost"
```

---

*— End of Document —*
