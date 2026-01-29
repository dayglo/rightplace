#!/bin/bash
#
# Audit Logging Demo Script
#
# This script demonstrates the audit logging functionality by:
# 1. Creating an inmate (logs INMATE_CREATED)
# 2. Updating the inmate (logs INMATE_UPDATED)
# 3. Enrolling a face (logs FACE_ENROLLED)
# 4. Creating a roll call (no audit log - just metadata)
# 5. Starting the roll call (logs ROLLCALL_STARTED)
# 6. Recording a verification (logs VERIFICATION_RECORDED)
# 7. Recording a manual override (logs MANUAL_OVERRIDE_USED)
# 8. Completing the roll call (logs ROLLCALL_COMPLETED)
# 9. Deleting the inmate (logs INMATE_DELETED)
# 10. Exporting and displaying the audit log
#

set -e  # Exit on error

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="${API_URL:-http://localhost:8000/api/v1}"
OFFICER_ID="${OFFICER_ID:-officer-demo}"

echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Audit Logging System Demo                      ║${NC}"
echo -e "${BLUE}╔════════════════════════════════════════════════════════╗${NC}"
echo ""
echo -e "${YELLOW}Officer ID:${NC} $OFFICER_ID"
echo -e "${YELLOW}API URL:${NC} $API_URL"
echo ""

# Function to print step headers
step() {
    echo ""
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}STEP $1: $2${NC}"
    echo -e "${GREEN}═══════════════════════════════════════════════════════${NC}"
}

# Function to print action
action() {
    echo -e "${YELLOW}→${NC} $1"
}

# Function to print success
success() {
    echo -e "${GREEN}✓${NC} $1"
}

# Check if server is running
echo -e "${YELLOW}Checking if server is running...${NC}"
if ! curl -s "$API_URL/health" > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠ Server not running at $API_URL${NC}"
    echo -e "${YELLOW}Please start the server first:${NC}"
    echo "  cd server"
    echo "  source .venv/bin/activate"
    echo "  uvicorn app.main:app --reload"
    exit 1
fi
success "Server is running"

# Wait for user to start
echo ""
read -p "Press ENTER to start the demo..."
echo ""

# ============================================================================
# STEP 1: Create Inmate
# ============================================================================
step "1" "Create Inmate (INMATE_CREATED)"
action "Creating inmate 'John Doe' (A12345)"

INMATE_RESPONSE=$(curl -s -X POST "$API_URL/inmates" \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: $OFFICER_ID" \
  -d '{
    "inmate_number": "A12345",
    "first_name": "John",
    "last_name": "Doe",
    "date_of_birth": "1990-01-01",
    "cell_block": "A",
    "cell_number": "101"
  }')

INMATE_ID=$(echo "$INMATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
success "Created inmate: $INMATE_ID"
echo "   Audit log should contain: INMATE_CREATED by $OFFICER_ID"

sleep 1

# ============================================================================
# STEP 2: Update Inmate
# ============================================================================
step "2" "Update Inmate (INMATE_UPDATED)"
action "Moving inmate to Cell B-202"

curl -s -X PUT "$API_URL/inmates/$INMATE_ID" \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: $OFFICER_ID" \
  -d '{
    "cell_block": "B",
    "cell_number": "202"
  }' > /dev/null

success "Updated inmate"
echo "   Audit log should contain: INMATE_UPDATED by $OFFICER_ID"
echo "   Details: {cell_block: B, cell_number: 202}"

sleep 1

# ============================================================================
# STEP 3: Create Location for Roll Call
# ============================================================================
step "3" "Create Location (Setup - not audited)"
action "Creating test location"

LOCATION_RESPONSE=$(curl -s -X POST "$API_URL/locations" \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: $OFFICER_ID" \
  -d '{
    "name": "Cell B-202",
    "type": "cell",
    "building": "Block B",
    "floor": 2,
    "capacity": 2
  }')

LOCATION_ID=$(echo "$LOCATION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
success "Created location: $LOCATION_ID"
echo "   (Locations are not audited currently)"

sleep 1

# ============================================================================
# STEP 4: Create Roll Call
# ============================================================================
step "4" "Create Roll Call (Setup - not audited)"
action "Creating morning roll call"

SCHEDULED_AT=$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%S")

ROLLCALL_RESPONSE=$(curl -s -X POST "$API_URL/rollcalls" \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: $OFFICER_ID" \
  -d "{
    \"name\": \"Morning Roll Call Demo\",
    \"scheduled_at\": \"$SCHEDULED_AT\",
    \"route\": [
      {
        \"id\": \"stop1\",
        \"location_id\": \"$LOCATION_ID\",
        \"order\": 1,
        \"expected_inmates\": [\"$INMATE_ID\"],
        \"status\": \"pending\"
      }
    ],
    \"officer_id\": \"$OFFICER_ID\",
    \"notes\": \"Demo roll call\"
  }")

ROLLCALL_ID=$(echo "$ROLLCALL_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
success "Created roll call: $ROLLCALL_ID"
echo "   (Roll call creation is not audited, only status changes)"

sleep 1

# ============================================================================
# STEP 5: Start Roll Call
# ============================================================================
step "5" "Start Roll Call (ROLLCALL_STARTED)"
action "Starting the roll call"

curl -s -X POST "$API_URL/rollcalls/$ROLLCALL_ID/start" \
  -H "X-Officer-ID: $OFFICER_ID" > /dev/null

success "Started roll call"
echo "   Audit log should contain: ROLLCALL_STARTED by $OFFICER_ID"
echo "   Details: {location: $LOCATION_ID, expected_stops: 1}"

sleep 1

# ============================================================================
# STEP 6: Record Regular Verification
# ============================================================================
step "6" "Record Verification (VERIFICATION_RECORDED)"
action "Recording successful face verification"

VERIFICATION_RESPONSE=$(curl -s -X POST "$API_URL/rollcalls/$ROLLCALL_ID/verification" \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: $OFFICER_ID" \
  -d "{
    \"inmate_id\": \"$INMATE_ID\",
    \"location_id\": \"$LOCATION_ID\",
    \"status\": \"verified\",
    \"confidence\": 0.95,
    \"is_manual_override\": false,
    \"notes\": \"Face match successful\"
  }")

VERIFICATION_ID=$(echo "$VERIFICATION_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
success "Recorded verification: $VERIFICATION_ID"
echo "   Audit log should contain: VERIFICATION_RECORDED by $OFFICER_ID"
echo "   Details: {confidence: 0.95, status: verified}"

sleep 1

# ============================================================================
# STEP 7: Record Manual Override
# ============================================================================
step "7" "Record Manual Override (MANUAL_OVERRIDE_USED)"
action "Recording manual override due to facial injury"

# Create another inmate for the override demo
INMATE2_RESPONSE=$(curl -s -X POST "$API_URL/inmates" \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: $OFFICER_ID" \
  -d '{
    "inmate_number": "A12346",
    "first_name": "Jane",
    "last_name": "Smith",
    "date_of_birth": "1992-05-15",
    "cell_block": "B",
    "cell_number": "203"
  }')

INMATE2_ID=$(echo "$INMATE2_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")

OVERRIDE_RESPONSE=$(curl -s -X POST "$API_URL/rollcalls/$ROLLCALL_ID/verification" \
  -H "Content-Type: application/json" \
  -H "X-Officer-ID: $OFFICER_ID" \
  -d "{
    \"inmate_id\": \"$INMATE2_ID\",
    \"location_id\": \"$LOCATION_ID\",
    \"status\": \"manual\",
    \"confidence\": 0.0,
    \"is_manual_override\": true,
    \"manual_override_reason\": \"facial_injury\",
    \"notes\": \"Inmate has bandage covering left side of face\"
  }")

OVERRIDE_ID=$(echo "$OVERRIDE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin)['id'])")
success "Recorded manual override: $OVERRIDE_ID"
echo "   Audit log should contain: MANUAL_OVERRIDE_USED by $OFFICER_ID"
echo "   Details: {reason: facial_injury, confidence: 0.0}"

sleep 1

# ============================================================================
# STEP 8: Complete Roll Call
# ============================================================================
step "8" "Complete Roll Call (ROLLCALL_COMPLETED)"
action "Completing the roll call"

curl -s -X POST "$API_URL/rollcalls/$ROLLCALL_ID/complete" \
  -H "X-Officer-ID: $OFFICER_ID" > /dev/null

success "Completed roll call"
echo "   Audit log should contain: ROLLCALL_COMPLETED by $OFFICER_ID"
echo "   Details: {total_stops: 1, verified_inmates: 2, progress_percentage: 100}"

sleep 1

# ============================================================================
# STEP 9: Delete Inmate
# ============================================================================
step "9" "Delete Inmate (INMATE_DELETED)"
action "Deleting inmate (cleanup)"

curl -s -X DELETE "$API_URL/inmates/$INMATE2_ID" \
  -H "X-Officer-ID: $OFFICER_ID" > /dev/null

success "Deleted inmate"
echo "   Audit log should contain: INMATE_DELETED by $OFFICER_ID"

sleep 1

# ============================================================================
# STEP 10: View Audit Log
# ============================================================================
step "10" "View Audit Log"
action "Fetching audit log from database"

echo ""
echo -e "${BLUE}════════════════════ AUDIT LOG ════════════════════${NC}"
echo ""

# Use Python to query the audit log directly
python3 << 'EOF'
import sqlite3
import json
from datetime import datetime, timedelta

# Connect to database
conn = sqlite3.connect('prison_rollcall.db')
conn.row_factory = sqlite3.Row
cursor = conn.cursor()

# Get recent audit entries (last 5 minutes)
cutoff = datetime.now() - timedelta(minutes=5)
cursor.execute("""
    SELECT
        timestamp,
        user_id,
        action,
        entity_type,
        entity_id,
        details,
        ip_address
    FROM audit_log
    WHERE timestamp > ?
    ORDER BY timestamp ASC
""", (cutoff.isoformat(),))

# Print each entry
for i, row in enumerate(cursor.fetchall(), 1):
    details = json.loads(row['details']) if row['details'] else {}

    print(f"{i}. [{row['timestamp']}]")
    print(f"   Action: {row['action']}")
    print(f"   User: {row['user_id']}")
    print(f"   Entity: {row['entity_type']} ({row['entity_id'][:8]}...)")
    print(f"   IP: {row['ip_address']}")

    if details:
        print(f"   Details: {json.dumps(details, indent=11)[0:100]}...")

    print()

conn.close()
EOF

echo -e "${BLUE}═══════════════════════════════════════════════════${NC}"
echo ""

# ============================================================================
# STEP 11: Export to CSV
# ============================================================================
step "11" "Export Audit Log to CSV"
action "Exporting audit log to CSV file"

EXPORT_FILE="audit_demo_$(date +%Y%m%d_%H%M%S).csv"
python3 scripts/export_audit.py --days 1 --output "$EXPORT_FILE"

if [ -f "$EXPORT_FILE" ]; then
    success "Exported to: $EXPORT_FILE"
    echo ""
    echo "First 10 lines of CSV:"
    echo ""
    head -n 10 "$EXPORT_FILE"
    echo ""
    echo "Total entries: $(tail -n +2 "$EXPORT_FILE" | wc -l)"
else
    echo "⚠ Export script not available"
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                 Demo Complete!                         ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════╝${NC}"
echo ""
echo "Actions audited:"
echo "  ✓ INMATE_CREATED"
echo "  ✓ INMATE_UPDATED"
echo "  ✓ ROLLCALL_STARTED"
echo "  ✓ VERIFICATION_RECORDED"
echo "  ✓ MANUAL_OVERRIDE_USED"
echo "  ✓ ROLLCALL_COMPLETED"
echo "  ✓ INMATE_DELETED"
echo ""
echo "All actions were performed by: $OFFICER_ID"
echo ""
echo "You can:"
echo "  1. Review the CSV file: cat $EXPORT_FILE"
echo "  2. Query specific actions: python3 -c \"from app.db.repositories.audit_repo import *\""
echo "  3. View in SQLite: sqlite3 prison_rollcall.db 'SELECT * FROM audit_log ORDER BY timestamp DESC LIMIT 10'"
echo ""
