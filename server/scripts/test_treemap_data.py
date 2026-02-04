#!/usr/bin/env python3
"""
Create test data for treemap endpoint demonstration.

Creates:
- 1 prison with hierarchy
- Sample inmates
- Sample rollcall with route
- Sample verifications

This provides everything needed to test the treemap endpoint.
"""
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime, timedelta


def generate_id():
    """Generate a UUID for database records."""
    return str(uuid.uuid4())


def create_location(conn, name, loc_type, parent_id=None, capacity=1, floor=0, building="Main"):
    """Create a location and return its ID."""
    loc_id = generate_id()

    conn.execute("""
        INSERT INTO locations (id, name, type, parent_id, capacity, floor, building, x_coord, y_coord)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (loc_id, name, loc_type, parent_id, capacity, floor, building, None, None))

    return loc_id


def create_inmate(conn, inmate_number, first_name, last_name, cell_id):
    """Create an inmate and return its ID."""
    inmate_id = generate_id()
    now = datetime.now().isoformat()

    conn.execute("""
        INSERT INTO inmates (
            id, inmate_number, first_name, last_name, date_of_birth,
            cell_block, cell_number, home_cell_id, is_enrolled, is_active,
            created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        inmate_id, inmate_number, first_name, last_name, "1990-01-01",
        "A", inmate_number[-3:], cell_id, 0, 1, now, now
    ))

    return inmate_id


def create_rollcall(conn, name, scheduled_at, route_json, officer_id):
    """Create a rollcall and return its ID."""
    rollcall_id = generate_id()

    conn.execute("""
        INSERT INTO roll_calls (
            id, name, status, scheduled_at, route, officer_id, notes
        ) VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        rollcall_id, name, "in_progress", scheduled_at, route_json, officer_id, "Test rollcall"
    ))

    return rollcall_id


def create_verification(conn, rollcall_id, inmate_id, location_id, status, confidence):
    """Create a verification record."""
    verification_id = generate_id()
    now = datetime.now().isoformat()

    conn.execute("""
        INSERT INTO verifications (
            id, roll_call_id, inmate_id, location_id, status,
            confidence, timestamp, is_manual_override
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        verification_id, rollcall_id, inmate_id, location_id,
        status, confidence, now, 0
    ))


def main():
    """Create test data for treemap demo."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Creating test data in: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Clear existing data
        print("\nClearing existing data...")
        cursor.execute("DELETE FROM verifications")
        cursor.execute("DELETE FROM roll_calls")
        cursor.execute("DELETE FROM inmates")
        cursor.execute("DELETE FROM location_connections")
        cursor.execute("DELETE FROM locations")
        conn.commit()

        # Create prison hierarchy
        print("\n📍 Creating prison hierarchy...")
        prison_id = create_location(conn, "HMP Test Prison", "prison", capacity=20)
        print(f"  ✅ Prison created")

        wing_id = create_location(conn, "A Wing", "wing", parent_id=prison_id, capacity=10)
        print(f"  ✅ Wing created")

        landing_id = create_location(conn, "Ground Floor", "landing", parent_id=wing_id, capacity=6)
        print(f"  ✅ Landing created")

        # Create 3 cells
        cells = []
        for i in range(1, 4):
            cell_id = create_location(
                conn, f"A1-{i:02d}", "cell",
                parent_id=landing_id, capacity=2, floor=0
            )
            cells.append(cell_id)
        print(f"  ✅ Created 3 cells")

        # Create inmates (2 per cell)
        print("\n👤 Creating inmates...")
        inmates = []
        for cell_idx, cell_id in enumerate(cells):
            for person in range(2):
                inmate_num = f"A{cell_idx+1:02d}{person+1}"
                inmate_id = create_inmate(
                    conn, inmate_num,
                    f"Person{cell_idx*2+person+1}",
                    "Testson",
                    cell_id
                )
                inmates.append((inmate_id, inmate_num, cell_id))
        print(f"  ✅ Created {len(inmates)} inmates")

        # Create rollcall
        print("\n📋 Creating rollcall...")
        scheduled_at = datetime.now() - timedelta(minutes=30)

        # Build route JSON
        import json
        route = []
        for idx, cell_id in enumerate(cells):
            expected = [inmate[1] for inmate in inmates if inmate[2] == cell_id]
            route.append({
                "id": generate_id(),
                "location_id": cell_id,
                "order": idx,
                "expected_inmates": expected,
                "status": "pending"
            })

        route_json = json.dumps(route)
        rollcall_id = create_rollcall(
            conn, "Morning Check",
            scheduled_at.isoformat(),
            route_json,
            "officer123"
        )
        print(f"  ✅ Rollcall created: {rollcall_id}")

        # Create some verifications
        print("\n✓ Creating verifications...")
        # Cell 1: All verified (GREEN)
        for inmate_id, inmate_num, cell_id in inmates[:2]:
            create_verification(conn, rollcall_id, inmate_id, cells[0], "verified", 0.95)
        print(f"  ✅ Cell 1: All verified (GREEN)")

        # Cell 2: One verified, one not found (RED)
        create_verification(conn, rollcall_id, inmates[2][0], cells[1], "verified", 0.92)
        create_verification(conn, rollcall_id, inmates[3][0], cells[1], "not_found", 0.0)
        print(f"  ✅ Cell 2: One failed (RED)")

        # Cell 3: No verifications yet (AMBER)
        print(f"  ⏳ Cell 3: No verifications (AMBER)")

        conn.commit()

        print("\n" + "="*60)
        print("✅ Test data created successfully!")
        print("="*60)
        print(f"\nRollcall ID: {rollcall_id}")
        print(f"Scheduled at: {scheduled_at.isoformat()}")
        print(f"\nTest the endpoint:")
        print(f'curl "http://localhost:8000/api/v1/treemap?rollcall_ids={rollcall_id}&timestamp={datetime.now().isoformat()}" | jq')
        print(f"\nExpected results:")
        print(f"  - Cell A1-01: GREEN (both inmates verified)")
        print(f"  - Cell A1-02: RED (one inmate not found)")
        print(f"  - Cell A1-03: AMBER (no verifications yet)")
        print(f"  - Landing, Wing, Prison: RED (aggregated from children)")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
