#!/bin/bash
#
# Reseed database with multiple prisons for treemap visualization demo
#
set -e  # Exit on any error

echo "========================================"
echo "Reseed Database - Multiple Prisons"
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

# Step 3: Seed with multiple prisons
echo "Step 3: Seeding multiple prisons (HMP Oakwood, HMP Nottingham, HMP Birmingham)..."
python scripts/seed_multiple_prisons.py
echo "  ✅ Prison locations seeded"
echo ""

# Step 4: Create inmates for the cells
echo "Step 4: Creating inmates (2 per cell)..."
python - << 'EOFPYTHON'
import sqlite3
import uuid
import random
from datetime import date, timedelta

conn = sqlite3.connect('data/prison_rollcall.db')
cursor = conn.cursor()

# Get all cells
cursor.execute("SELECT id, name FROM locations WHERE type = 'cell'")
cells = cursor.fetchall()

first_names = ["James", "John", "Robert", "Michael", "David", "William", "Richard", "Thomas"]
last_names = ["Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis"]

inmate_count = 0
for cell_id, cell_name in cells:
    for i in range(2):  # 2 inmates per cell
        inmate_id = str(uuid.uuid4())
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        inmate_number = f"{random.choice('ABCDEFGH')}{random.randint(1000, 9999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
        age_years = random.randint(25, 65)
        dob = date.today() - timedelta(days=age_years * 365)
        now = date.today().isoformat()
        
        cursor.execute("""
            INSERT INTO inmates (id, inmate_number, first_name, last_name, date_of_birth, 
                               cell_block, cell_number, home_cell_id, is_enrolled, is_active, 
                               created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 1, ?, ?)
        """, (inmate_id, inmate_number, first_name, last_name, dob.isoformat(),
              cell_name[:2], cell_name, cell_id, now, now))
        inmate_count += 1

conn.commit()
print(f"  ✅ Created {inmate_count} inmates")
conn.close()
EOFPYTHON
echo ""

# Step 5: Verify the database
echo "========================================"
echo "Verification"
echo "========================================"
python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')

print('Database Statistics:')
cursor = conn.cursor()

# Count locations by type
cursor.execute('SELECT type, COUNT(*) FROM locations GROUP BY type ORDER BY type')
print('  Locations by type:')
for loc_type, count in cursor.fetchall():
    print(f'    - {loc_type}: {count}')

# Count inmates
cursor.execute('SELECT COUNT(*) FROM inmates')
inmate_count = cursor.fetchone()[0]
print(f'  ✅ Total inmates: {inmate_count}')

# Count inmates by prison
cursor.execute('''
    SELECT l_prison.name, COUNT(i.id)
    FROM inmates i
    JOIN locations l_cell ON i.home_cell_id = l_cell.id
    JOIN locations l_landing ON l_cell.parent_id = l_landing.id
    JOIN locations l_wing ON l_landing.parent_id = l_wing.id
    JOIN locations l_houseblock ON l_wing.parent_id = l_houseblock.id
    JOIN locations l_prison ON l_houseblock.parent_id = l_prison.id
    WHERE l_prison.type = \"prison\"
    GROUP BY l_prison.name
    ORDER BY l_prison.name
''')
print('  Inmates by prison:')
for prison, count in cursor.fetchall():
    print(f'    - {prison}: {count}')

conn.close()
"
echo ""
echo "========================================"
echo "✅ Database ready for treemap visualization!"
echo "========================================"
