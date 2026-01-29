# Audit Logging Demo Guide

This guide shows you how to demonstrate the audit logging functionality.

---

## Quick Start: Automated Demo

### Prerequisites
1. Server must be running
2. Database initialized with migrations

### Run the Demo

```bash
cd server

# Start the server in one terminal
source .venv/bin/activate
uvicorn app.main:app --reload

# In another terminal, run the demo script
source .venv/bin/activate
./scripts/demo_audit_api.sh
```

The script will:
1. ✅ Create an inmate → logs `INMATE_CREATED`
2. ✅ Update the inmate → logs `INMATE_UPDATED`
3. ✅ Create a roll call
4. ✅ Start the roll call → logs `ROLLCALL_STARTED`
5. ✅ Record a verification → logs `VERIFICATION_RECORDED`
6. ✅ Record a manual override → logs `MANUAL_OVERRIDE_USED`
7. ✅ Complete the roll call → logs `ROLLCALL_COMPLETED`
8. ✅ Delete the inmate → logs `INMATE_DELETED`
9. ✅ Display the audit log
10. ✅ Export to CSV

All actions are performed by the officer: `officer-demo`

---

## Manual Demo: Step-by-Step

Use this for interactive demonstrations or when you want to show specific features.

### Setup

```bash
# Terminal 1: Start the server
cd server
source .venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Run commands
cd server
source .venv/bin/activate
```

---

### Demo Scenario: "A Day in the Life of Officer Alice"

#### 1. Create a New Inmate

**Story:** "A new prisoner arrives at the facility."

```bash
curl -X POST http://localhost:8000/api/v1/inmates \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: officer-alice" \
  -d '{
    "inmate_number": "A99999",
    "first_name": "Michael",
    "last_name": "Johnson",
    "date_of_birth": "1985-03-15",
    "cell_block": "C",
    "cell_number": "305"
  }'
```

**What gets logged:**
- Action: `INMATE_CREATED`
- User: `officer-alice`
- Details: `{inmate_number: "A99999", name: "Michael Johnson"}`

Save the returned `id` for next steps!

---

#### 2. Enroll the Inmate's Face

**Story:** "Officer Alice takes a photo for face recognition."

```bash
# First, create a test image (or use a real one)
# For demo, we'll use a sample from the test fixtures
INMATE_ID="<paste the id from step 1>"

curl -X POST http://localhost:8000/api/v1/enrollment/$INMATE_ID \
  -H "X-Officer-ID: officer-alice" \
  -F "image=@tests/fixtures/faces/Aaron_Eckhart_0001.jpg"
```

**What gets logged:**
- Action: `FACE_ENROLLED`
- User: `officer-alice`
- Details: `{quality: 0.95, model_version: "Facenet512", file_size_bytes: 45123}`

---

#### 3. Update Inmate Information

**Story:** "The prisoner is moved to a different cell."

```bash
curl -X PUT http://localhost:8000/api/v1/inmates/$INMATE_ID \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: officer-alice" \
  -d '{
    "cell_block": "D",
    "cell_number": "410"
  }'
```

**What gets logged:**
- Action: `INMATE_UPDATED`
- User: `officer-alice`
- Details: `{updated_fields: {cell_block: "D", cell_number: "410"}}`

---

#### 4. Create and Start a Roll Call

**Story:** "Officer Alice begins the morning roll call."

```bash
# Create the roll call (not audited)
ROLLCALL_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/rollcalls \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: officer-alice" \
  -d '{
    "name": "Morning Roll Call",
    "scheduled_at": "'"$(date -u -d '+1 hour' +%Y-%m-%dT%H:%M:%S)"'",
    "route": [
      {
        "id": "stop1",
        "location_id": "cell-305",
        "order": 1,
        "expected_inmates": ["'$INMATE_ID'"],
        "status": "pending"
      }
    ],
    "officer_id": "officer-alice"
  }')

# Extract the roll call ID
ROLLCALL_ID=$(echo $ROLLCALL_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Start it (THIS IS AUDITED)
curl -X POST http://localhost:8000/api/v1/rollcalls/$ROLLCALL_ID/start \
  -H "X-Officer-ID: officer-alice"
```

**What gets logged:**
- Action: `ROLLCALL_STARTED`
- User: `officer-alice`
- Details: `{location: "cell-305", expected_stops: 1}`

---

#### 5. Record a Successful Verification

**Story:** "Face recognition confirms Michael Johnson is in his cell."

```bash
curl -X POST http://localhost:8000/api/v1/rollcalls/$ROLLCALL_ID/verification \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: officer-alice" \
  -d '{
    "inmate_id": "'$INMATE_ID'",
    "location_id": "cell-305",
    "status": "verified",
    "confidence": 0.96,
    "is_manual_override": false,
    "notes": "Face match successful"
  }'
```

**What gets logged:**
- Action: `VERIFICATION_RECORDED`
- User: `officer-alice`
- Details: `{inmate_id: "...", confidence: 0.96, status: "verified"}`

---

#### 6. Record a Manual Override

**Story:** "An inmate has a facial injury and can't be verified by face recognition."

```bash
# Create another inmate for this demo
INJURED_RESPONSE=$(curl -s -X POST http://localhost:8000/api/v1/inmates \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: officer-alice" \
  -d '{
    "inmate_number": "A99998",
    "first_name": "David",
    "last_name": "Wilson",
    "date_of_birth": "1990-07-22",
    "cell_block": "C",
    "cell_number": "306"
  }')

INJURED_ID=$(echo $INJURED_RESPONSE | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

# Record manual override
curl -X POST http://localhost:8000/api/v1/rollcalls/$ROLLCALL_ID/verification \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: officer-alice" \
  -d '{
    "inmate_id": "'$INJURED_ID'",
    "location_id": "cell-306",
    "status": "manual",
    "confidence": 0.0,
    "is_manual_override": true,
    "manual_override_reason": "facial_injury",
    "notes": "Inmate has bandage covering right eye after altercation"
  }'
```

**What gets logged:**
- Action: `MANUAL_OVERRIDE_USED` ⚠️ (High sensitivity!)
- User: `officer-alice`
- Details: `{manual_override_reason: "facial_injury", confidence: 0.0, notes: "..."}`

---

#### 7. Complete the Roll Call

**Story:** "Officer Alice finishes the roll call."

```bash
curl -X POST http://localhost:8000/api/v1/rollcalls/$ROLLCALL_ID/complete \
  -H "X-Officer-ID: officer-alice"
```

**What gets logged:**
- Action: `ROLLCALL_COMPLETED`
- User: `officer-alice`
- Details: `{total_stops: 2, verified_inmates: 2, progress_percentage: 100}`

---

#### 8. View the Audit Log

**Option A: Using the export script**

```bash
python scripts/export_audit.py --days 1 --output demo.csv
cat demo.csv
```

**Option B: Direct database query**

```bash
sqlite3 prison_rollcall.db << 'EOF'
.headers on
.mode column
SELECT
    datetime(timestamp) as time,
    user_id as officer,
    action,
    entity_type,
    substr(entity_id, 1, 8) as entity
FROM audit_log
WHERE user_id = 'officer-alice'
ORDER BY timestamp DESC
LIMIT 10;
EOF
```

**Option C: Using Python**

```python
from app.db.database import get_connection
from app.db.repositories.audit_repo import AuditRepository

conn = get_connection('prison_rollcall.db')
audit_repo = AuditRepository(conn)

# Get all actions by officer-alice
actions = audit_repo.get_by_user('officer-alice', limit=20)

for entry in actions:
    print(f"[{entry.timestamp}] {entry.action} - {entry.entity_type}")
    print(f"  Details: {entry.details}")
    print()
```

---

## Demo Talking Points

### Key Features to Highlight

1. **Who, What, When, Where**
   - Every action captures the officer ID, action type, timestamp, and IP address
   - Full audit trail for compliance and accountability

2. **Tamper-Proof**
   - Audit log is append-only
   - Cannot be modified or deleted by officers
   - Timestamps are automatically generated

3. **High-Sensitivity Actions Flagged**
   - Manual overrides are logged separately as `MANUAL_OVERRIDE_USED`
   - Easy to query all overrides for review
   - Includes reason and notes

4. **Complete Details**
   - Not just "inmate updated" but exactly which fields changed
   - Face enrollment includes quality scores and model versions
   - Roll call completion includes progress statistics

5. **Easy Export**
   - CSV export for compliance reporting
   - Integration with audit systems
   - Date range filtering

### Questions to Answer

**Q: "What if an officer forgets to include their ID?"**
A: The system defaults to `"unknown"` and still logs the action. In production, this would be enforced by JWT authentication.

**Q: "Can officers delete their audit trail?"**
A: No! The audit log is append-only. Only database administrators with direct DB access could modify it (and that would be logged by the database itself).

**Q: "How far back does the audit log go?"**
A: Forever, unless you have a retention policy. You can export and archive old logs.

**Q: "What actions are NOT audited?"**
A: Read-only operations (GET requests) and metadata-only changes like creating a roll call. We only audit security-sensitive operations.

---

## Advanced Demo: Forensic Investigation

**Scenario:** "An inmate claims they were marked as absent when they were present."

```bash
# 1. Find all verifications for this inmate
INMATE_NUMBER="A99999"

# Get inmate ID
INMATE_ID=$(curl -s http://localhost:8000/api/v1/inmates | \
  python3 -c "import sys, json; inmates = json.load(sys.stdin); print([i['id'] for i in inmates if i['inmate_number']=='$INMATE_NUMBER'][0])")

# 2. Query audit log for all actions on this inmate
sqlite3 prison_rollcall.db << EOF
.headers on
.mode table
SELECT
    datetime(timestamp) as time,
    user_id as officer,
    action,
    json_extract(details, '$.status') as verification_status,
    json_extract(details, '$.confidence') as confidence
FROM audit_log
WHERE entity_id = '$INMATE_ID'
   OR json_extract(details, '$.inmate_id') = '$INMATE_ID'
ORDER BY timestamp;
EOF
```

This shows:
- When the inmate was created
- All face enrollments
- All verifications during roll calls
- Any manual overrides
- Who performed each action

---

## Clean Up After Demo

```bash
# Delete test data (this will also be audited!)
curl -X DELETE http://localhost:8000/api/v1/inmates/$INMATE_ID \
  -H "X-Officer-ID: officer-alice"

curl -X DELETE http://localhost:8000/api/v1/inmates/$INJURED_ID \
  -H "X-Officer-ID: officer-alice"

# The audit log remains!
```

---

## Troubleshooting

### Server not starting
```bash
cd server
source .venv/bin/activate
python -m app.main
```

### Database not found
```bash
# Initialize the database
cd server
source .venv/bin/activate
python scripts/init_db.py
```

### No audit entries appearing
1. Check that middleware is registered: `grep -n "RequestContextMiddleware" app/main.py`
2. Check that audit migration ran: `sqlite3 prison_rollcall.db ".tables" | grep audit`
3. Verify you're sending the `X-Officer-ID` header

---

## Demo Checklist

Before the demo:
- [ ] Server is running
- [ ] Database is initialized
- [ ] Test images available (if demoing face enrollment)
- [ ] Terminal windows arranged for visibility

During the demo:
- [ ] Show the API requests with `X-Officer-ID` header
- [ ] Emphasize security-sensitive actions (create, update, delete, override)
- [ ] Show the audit log after each major action
- [ ] Demonstrate CSV export
- [ ] Show a manual override scenario

After the demo:
- [ ] Export final audit log as evidence
- [ ] Show how to query for specific actions
- [ ] Discuss production authentication integration
