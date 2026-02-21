#!/usr/bin/env python3
"""
Generate rollcalls for the past N days.

Creates Morning Unlock, Midday Count, and Evening Lock-up rollcalls
for each prison in the database.

Usage:
    cd server
    source .venv/bin/activate
    python scripts/generate_rollcalls.py
"""
import json
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

# Configuration
ROLLCALL_DAYS = 3  # Number of days of rollcall history to generate

ROLLCALL_TYPES = [
    ("Morning Unlock", "07:30"),
    ("Midday Count", "12:00"),
    ("Evening Lock-up", "17:30"),
]


def generate_id():
    """Generate a UUID."""
    return str(uuid.uuid4())


def generate_rollcalls():
    """Generate rollcalls for all prisons."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Generating rollcalls for: {db_path}")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Run seed scripts first.")
        return

    conn = sqlite3.connect(db_path)

    try:
        # Clear existing rollcalls and verifications
        print("\nClearing existing rollcalls and verifications...")
        conn.execute("DELETE FROM verifications")
        conn.execute("DELETE FROM roll_calls")
        conn.commit()

        # Get all prisons
        cursor = conn.execute("SELECT id, name FROM locations WHERE type = 'prison'")
        prisons = cursor.fetchall()
        print(f"Found {len(prisons)} prisons")

        # Get all cells grouped by prison (building)
        cursor = conn.execute("""
            SELECT id, name, building FROM locations
            WHERE type = 'cell'
            ORDER BY building, name
        """)
        cells_by_prison = {}
        for cell_id, cell_name, building in cursor.fetchall():
            if building not in cells_by_prison:
                cells_by_prison[building] = []
            cells_by_prison[building].append((cell_id, cell_name))

        # Get inmates grouped by cell
        cursor = conn.execute("SELECT id, home_cell_id FROM inmates WHERE home_cell_id IS NOT NULL")
        inmates_by_cell = {}
        for inmate_id, cell_id in cursor.fetchall():
            if cell_id not in inmates_by_cell:
                inmates_by_cell[cell_id] = []
            inmates_by_cell[cell_id].append(inmate_id)

        total_rollcalls = 0
        today = date.today()
        start_date = today - timedelta(days=ROLLCALL_DAYS - 1)

        for day_offset in range(ROLLCALL_DAYS):
            current_date = start_date + timedelta(days=day_offset)
            date_str = current_date.strftime("%Y-%m-%d")

            for prison_id, prison_name in prisons:
                prison_cells = cells_by_prison.get(prison_name, [])

                for rollcall_name, scheduled_time in ROLLCALL_TYPES:
                    rollcall_id = generate_id()
                    full_name = f"{rollcall_name} - {date_str}"
                    scheduled_at = f"{date_str}T{scheduled_time}:00"

                    # Build route (all cells in order)
                    route = []
                    for idx, (cell_id, cell_name) in enumerate(prison_cells):
                        expected_ids = inmates_by_cell.get(cell_id, [])
                        route.append({
                            "id": generate_id(),
                            "location_id": cell_id,
                            "order": idx,
                            "expected_inmates": expected_ids,
                            "status": "completed"
                        })

                    # Calculate timing
                    started_at = f"{date_str}T{scheduled_time}:02"
                    num_inmates = sum(len(inmates_by_cell.get(c[0], [])) for c in prison_cells)
                    total_seconds = int(num_inmates * 3)  # ~3 seconds per verification

                    start_dt = datetime.fromisoformat(started_at)
                    completed_dt = start_dt + timedelta(seconds=total_seconds)
                    completed_at = completed_dt.isoformat()

                    # Insert rollcall
                    conn.execute("""
                        INSERT INTO roll_calls
                        (id, name, status, scheduled_at, started_at, completed_at, route, officer_id, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        rollcall_id, full_name, "completed", scheduled_at, started_at,
                        completed_at, json.dumps(route), "officer_seed", ""
                    ))
                    total_rollcalls += 1

            print(f"  ✅ Generated rollcalls for {date_str}")

        conn.commit()
        print(f"\n✅ Created {total_rollcalls} rollcalls")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    generate_rollcalls()
