#!/bin/bash
#
# Clean and reseed the database for a fresh rollcall-ready state
#
set -e  # Exit on any error

echo "========================================"
echo "Clean Database Reseed"
echo "========================================"
echo ""

# Navigate to server directory
cd "$(dirname "$0")/.."

# Activate virtualenv
source .venv/bin/activate

# Step 1: Delete the database entirely
echo "Step 1: Removing existing database..."
if [ -f "data/prison_rollcall.db" ]; then
    rm data/prison_rollcall.db
    echo "  ✅ Deleted old database"
else
    echo "  ℹ️  No existing database found"
fi
echo ""

# Step 2: Recreate the database schema
echo "Step 2: Creating fresh database schema..."
python scripts/setup_db.py
echo "  ✅ Database schema created"
echo ""

# Step 3: Seed with HMP Oakwood locations
echo "Step 3: Seeding HMP Oakwood locations..."
python scripts/seed_hmp_oakwood.py
echo "  ✅ Locations seeded"
echo ""

# Step 4: Generate prisoners and schedules
echo "Step 4: Generating prisoners and schedules..."
python scripts/generate_schedules.py
echo "  ✅ Prisoners and schedules created"
echo ""

# Step 5: Verify the database
echo "========================================"
echo "Verification"
echo "========================================"
python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')

tables = {
    'inmates': 1600,
    'locations': None,
    'location_connections': None,
    'schedule_entries': 100000,
    'houseblocks': 3,
    'wings': 5,
    'landings': 15,
}

print('Database Statistics:')
for table, expected in tables.items():
    if table == 'houseblocks':
        count = conn.execute('SELECT COUNT(*) FROM locations WHERE type=\"houseblock\"').fetchone()[0]
    elif table == 'wings':
        count = conn.execute('SELECT COUNT(*) FROM locations WHERE type=\"wing\"').fetchone()[0]
    elif table == 'landings':
        count = conn.execute('SELECT COUNT(*) FROM locations WHERE type=\"landing\"').fetchone()[0]
    else:
        count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]

    status = ''
    if expected:
        if table == 'schedule_entries' and count > expected:
            status = '✅'
        elif count == expected:
            status = '✅'
        elif abs(count - expected) <= 10:  # Allow small variance
            status = '⚠️ '
        else:
            status = '❌'
    else:
        status = 'ℹ️ '

    expected_str = f' (expected ~{expected})' if expected else ''
    print(f'  {status} {table}: {count}{expected_str}')

conn.close()
"
echo ""
echo "========================================"
echo "✅ Database is clean and ready for rollcall!"
echo "========================================"
