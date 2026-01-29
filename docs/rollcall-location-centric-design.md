# Location-Centric Roll Call System Design

**Version 1.0 | January 2026**

## Overview

This document describes the location-centric roll call system for Prison Roll Call. The system allows officers to select a location (e.g., Houseblock 1) and automatically generates an optimal walking route through all child locations, with schedule-aware prisoner expectations and priority handling for imminent appointments.

---

## Workflow

### Officer's Perspective

1. **Select parent location**: "I need to do a roll call of Houseblock 1"
2. **View generated route**: System shows all child locations (wings, landings, cells) within Houseblock 1
3. **Empty location handling**: Locations with scheduled prisoners are highlighted; empty locations are greyed out
4. **Walking route**: System provides an optimal walking route through occupied locations
5. **At each cell, officer sees**:
   - Who should be there (based on schedule)
   - If cell is empty: why (prisoner at work/healthcare with ETA)
   - Prisoners with imminent appointments shown at top (priority verification)

---

## Data Model Changes

### 1. Add `home_cell_id` to Inmates

```sql
-- Migration 005: Add home_cell_id to inmates
ALTER TABLE inmates ADD COLUMN home_cell_id TEXT REFERENCES locations(id);

-- Index for efficient lookups
CREATE INDEX idx_inmates_home_cell ON inmates(home_cell_id);
```

This links each prisoner to their assigned cell (a location), not just string "A-101".

### 2. Enhanced Inmate Model

```python
class Inmate(BaseModel):
    id: str
    inmate_number: str
    first_name: str
    last_name: str
    date_of_birth: date
    
    # Home cell (primary location)
    home_cell_id: str | None = None  # FK to locations
    cell_block: str   # Legacy/display: "A"
    cell_number: str  # Legacy/display: "101"
    
    # ... other fields
```

---

## Location Hierarchy

Locations use `parent_id` for hierarchy:

```
Houseblock 1 (type: HOUSEBLOCK)
├── A Wing (type: WING, parent: Houseblock 1)
│   ├── 1s Landing (type: LANDING, parent: A Wing)
│   │   ├── A1-01 (type: CELL, parent: 1s Landing)
│   │   ├── A1-02 (type: CELL)
│   │   └── ...
│   ├── 2s Landing
│   └── 3s Landing
├── B Wing
└── ...
```

---

## API Design

### 1. Generate Roll Call Route

```
POST /api/v1/rollcalls/generate
```

**Request:**
```json
{
  "location_id": "houseblock-1-id",    // Parent location
  "scheduled_at": "2026-01-29T08:30:00Z",  // When roll call will occur
  "include_empty": false,              // Include locations with no scheduled prisoners?
  "name": "Morning Roll Call - HB1",
  "officer_id": "officer-001"
}
```

**Response:**
```json
{
  "rollcall": {
    "id": "rc-123",
    "name": "Morning Roll Call - HB1",
    "status": "scheduled",
    "route": [
      {
        "order": 0,
        "location_id": "a1-01",
        "location_name": "A1-01",
        "location_type": "cell",
        "building": "Houseblock 1",
        "floor": 1,
        "is_occupied": true,
        "expected_count": 1,
        "walking_from_previous": {
          "distance_meters": 0,
          "time_seconds": 0
        }
      },
      {
        "order": 1,
        "location_id": "a1-02",
        "location_name": "A1-02",
        "is_occupied": true,
        "expected_count": 2,
        "walking_from_previous": {
          "distance_meters": 3,
          "time_seconds": 5
        }
      },
      {
        "order": 2,
        "location_id": "a1-03",
        "location_name": "A1-03",
        "is_occupied": false,
        "expected_count": 0
      }
    ]
  },
  "summary": {
    "total_locations": 48,
    "occupied_locations": 42,
    "empty_locations": 6,
    "total_prisoners_expected": 45,
    "estimated_time_seconds": 1200
  }
}
```

### 2. Get Expected Prisoners at Location (with Priority)

```
GET /api/v1/rollcalls/{rollcall_id}/stops/{location_id}/expected
```

**Response:**
```json
{
  "location_id": "a1-01",
  "location_name": "A1-01",
  "expected_prisoners": [
    {
      "inmate": {
        "id": "inmate-123",
        "inmate_number": "HO4521",
        "first_name": "John",
        "last_name": "Smith",
        "is_enrolled": true
      },
      "home_cell_id": "a1-01",
      "is_at_home_cell": true,
      "current_activity": "lock_up",
      "next_appointment": {
        "activity_type": "healthcare",
        "location_name": "Healthcare Unit",
        "start_time": "09:00",
        "minutes_until": 25,
        "is_urgent": true
      },
      "priority_score": 95
    },
    {
      "inmate": {
        "id": "inmate-456",
        "inmate_number": "HO7892",
        "first_name": "James",
        "last_name": "Wilson"
      },
      "is_at_home_cell": true,
      "current_activity": "lock_up",
      "next_appointment": null,
      "priority_score": 50
    }
  ],
  "absent_but_expected": [],
  "verification_status": {
    "total_expected": 2,
    "verified": 0,
    "pending": 2
  }
}
```

### 3. Get Absent Prisoner Context (Why Empty?)

When a cell appears empty during roll call:

```
GET /api/v1/inmates/{inmate_id}/whereabouts
```

**Response:**
```json
{
  "inmate_id": "inmate-789",
  "inmate_number": "HO1234",
  "name": "Robert Brown",
  "home_cell": {
    "id": "a1-05",
    "name": "A1-05"
  },
  "current_location": {
    "location": {
      "id": "kitchen-id",
      "name": "Kitchen"
    },
    "activity_type": "work",
    "since": "07:30",
    "until": "11:30"
  },
  "is_absence_explained": true,
  "explanation": "Assigned to Kitchen work detail until 11:30"
}
```

---

## Priority Calculation Algorithm

```python
def calculate_priority(inmate, current_time) -> int:
    """
    Calculate priority score for verification order.
    Higher score = verify sooner.
    """
    score = 50  # Base score
    
    next_apt = get_next_appointment(inmate, current_time)
    if next_apt:
        minutes_until = (next_apt.start_time - current_time).minutes
        
        if minutes_until < 15:
            score += 50  # Very urgent
        elif minutes_until < 30:
            score += 40  # Urgent  
        elif minutes_until < 60:
            score += 20  # Soon
    
    # Healthcare appointments get extra priority
    if next_apt and next_apt.activity_type == "healthcare":
        score += 10
    
    # Visits (family) get priority too
    if next_apt and next_apt.activity_type == "visits":
        score += 5
    
    return min(score, 100)
```

### Priority Levels

| Minutes Until Appointment | Activity Type | Priority Score |
|---------------------------|---------------|----------------|
| < 15 min | Healthcare | 100 |
| < 15 min | Visits | 95 |
| < 15 min | Other | 100 |
| 15-30 min | Healthcare | 90 |
| 15-30 min | Visits | 85 |
| 15-30 min | Other | 90 |
| 30-60 min | Any | 70 |
| > 60 min or none | Any | 50 |

---

## UI Display Design

```
┌────────────────────────────────────────────────────┐
│ Roll Call: Morning - Houseblock 1                  │
│ Progress: 15/48 locations │ 23/45 prisoners       │
├────────────────────────────────────────────────────┤
│                                                    │
│ ROUTE                           CURRENT: A1-12    │
│ ┌─────────────────────────────────────────────┐   │
│ │ ✅ A1-01  ✅ A1-02  ✅ A1-03  ⬜ A1-04      │   │
│ │ ⬜ A1-05  ⬜ A1-06  ░░ A1-07  ░░ A1-08      │   │
│ │ ...                                         │   │
│ └─────────────────────────────────────────────┘   │
│                                                    │
│ Legend: ✅ Complete  ⬜ Pending  ░░ Empty (skip)   │
│                                                    │
├────────────────────────────────────────────────────┤
│ CURRENT LOCATION: A1-12  (2 expected)             │
│                                                    │
│ ⚠️ URGENT (Healthcare at 09:00)                   │
│ ┌──────────────────────────────────────────────┐  │
│ │ 👤 HO4521 John SMITH     [VERIFY] [SKIP]    │  │
│ │    Next: Healthcare Unit in 25 mins          │  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
│ ┌──────────────────────────────────────────────┐  │
│ │ 👤 HO7892 James WILSON   [VERIFY] [SKIP]    │  │
│ │    No upcoming appointments                  │  │
│ └──────────────────────────────────────────────┘  │
│                                                    │
└────────────────────────────────────────────────────┘
```

---

## Implementation Phases

### Phase 1: Database & Models
1. Add migration 005 for `home_cell_id`
2. Update Inmate model with `home_cell_id`
3. Update seed script to link inmates to home cells

### Phase 2: API Endpoints
1. `POST /rollcalls/generate` - Generate route from location hierarchy
2. `GET /rollcalls/{id}/stops/{location_id}/expected` - Prisoners at stop
3. `GET /inmates/{id}/whereabouts` - Where is prisoner right now

### Phase 3: Priority System
1. Add priority calculation service
2. Integrate with expected prisoners endpoint
3. Sort by priority_score descending

### Phase 4: Web UI
1. Location selector (tree view of hierarchy)
2. Roll call route display with greyed empties
3. Current stop view with priority-sorted prisoners

---

## Database Queries

### Get All Child Locations (Recursive)

```sql
WITH RECURSIVE location_tree AS (
    -- Base case: the selected location
    SELECT id, name, type, parent_id, 0 as depth
    FROM locations
    WHERE id = :parent_location_id
    
    UNION ALL
    
    -- Recursive case: children
    SELECT l.id, l.name, l.type, l.parent_id, lt.depth + 1
    FROM locations l
    JOIN location_tree lt ON l.parent_id = lt.id
)
SELECT * FROM location_tree
WHERE type = 'cell'  -- Only leaf nodes (cells)
ORDER BY name;
```

### Get Prisoners Expected at Location at Time

```sql
SELECT 
    i.*,
    s.activity_type,
    s.start_time,
    s.end_time,
    s.location_id as scheduled_location_id
FROM inmates i
LEFT JOIN schedule_entries s ON i.id = s.inmate_id
WHERE (
    -- At home cell during lock-up
    (i.home_cell_id = :location_id AND s.activity_type = 'lock_up')
    OR
    -- Scheduled to be at this location
    (s.location_id = :location_id)
)
AND s.day_of_week = :day_of_week
AND s.start_time <= :time
AND s.end_time > :time;
```

---

*End of Design Document*
