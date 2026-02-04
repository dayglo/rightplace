#!/usr/bin/env python3
"""
Seed the database with multiple dummy prisons for treemap visualization demo.

Creates 3 prisons with simplified hierarchies for testing the treemap feature:
- HMP Oakwood
- HMP Nottingham
- HMP Birmingham

Each prison has a simplified structure for demo purposes.
"""
import sqlite3
import uuid
from pathlib import Path
from datetime import datetime


def generate_id():
    """Generate a UUID for database records."""
    return str(uuid.uuid4())


def create_location(conn, name, loc_type, parent_id=None, capacity=1, floor=0, building="Main", x=None, y=None):
    """Create a location and return its ID."""
    loc_id = generate_id()

    conn.execute("""
        INSERT INTO locations (id, name, type, parent_id, capacity, floor, building, x_coord, y_coord)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (loc_id, name, loc_type, parent_id, capacity, floor, building, x, y))

    return loc_id


def seed_prison(conn, prison_name, x_offset=0):
    """
    Seed a single prison with COMPLETE hierarchy including ALL facility types.

    Structure:
    - Prison
      - Houseblock 1 (residential with wings/landings/cells)
      - Houseblock 2 (residential with wings/landings/cells)
      - Kitchen, Workshops, Visits, Healthcare, etc. (facilities)

    Total: 80 prisoners per prison (40 per houseblock)
    """
    print(f"\n📍 Creating {prison_name}...")

    # Create prison
    prison_id = create_location(
        conn, prison_name, "prison",
        capacity=80, building=prison_name, x=x_offset, y=0
    )
    print(f"  ✅ Created prison: {prison_name}")

    # ===== HOUSEBLOCKS (Residential) =====
    houseblock_names = ["Houseblock 1", "Houseblock 2"]
    wing_configs = [
        ("A Wing", "B Wing"),  # Houseblock 1 wings
        ("C Wing", "D Wing"),  # Houseblock 2 wings
    ]

    for hb_idx, hb_name in enumerate(houseblock_names):
        # Create houseblock
        hb_id = create_location(
            conn, hb_name, "houseblock",
            parent_id=prison_id,
            capacity=40, building=prison_name,
            x=x_offset + hb_idx * 200, y=50
        )
        print(f"    ✅ Created {hb_name}")

        # Create wings in this houseblock
        for wing_name in wing_configs[hb_idx]:
            wing_id = create_location(
                conn, wing_name, "wing",
                parent_id=hb_id,
                capacity=20, building=prison_name
            )
            print(f"      ✅ Created {wing_name}")

            # Create 2 landings per wing
            for landing_num in range(1, 3):
                landing_name = f"Landing {landing_num}"
                landing_id = create_location(
                    conn, landing_name, "landing",
                    parent_id=wing_id,
                    capacity=10, floor=landing_num - 1, building=prison_name
                )
                print(f"        ✅ Created {landing_name}")

                # Create 5 cells per landing
                wing_letter = wing_name[0]
                for cell_num in range(1, 6):
                    cell_name = f"{wing_letter}{landing_num}-{cell_num:02d}"
                    create_location(
                        conn, cell_name, "cell",
                        parent_id=landing_id,
                        capacity=2, floor=landing_num - 1, building=prison_name
                    )

                print(f"          Created 5 cells (10 capacity)")

    # ===== FACILITIES (Non-residential - same level as houseblocks) =====
    print(f"  📦 Creating facilities...")

    facilities = [
        ("Kitchen", "kitchen", 0),
        ("Main Workshop", "workshop", 0),
        ("Workshop 2", "workshop", 0),
        ("Visits Building", "visits", 0),
        ("Healthcare Unit", "healthcare", 0),
        ("Drug Recovery Unit", "vpu", 0),
        ("Education Block", "education", 0),
        ("Sports Centre", "gym", 0),
        ("Chapel / Multi-faith Room", "chapel", 0),
        ("Reception", "reception", 0),
        ("Induction Unit", "induction", 0),
        ("Admin Offices", "admin", 0),
        ("Segregation Unit (CSU)", "segregation", 0),
        ("Exercise Yard 1", "yard", 0),
        ("Exercise Yard 2", "yard", 0),
    ]

    for facility_name, facility_type, capacity in facilities:
        create_location(
            conn, facility_name, facility_type,
            parent_id=prison_id,  # Direct child of prison (same level as houseblocks)
            capacity=capacity,
            building=prison_name
        )
        print(f"    ✅ Created {facility_name} ({facility_type})")

    return prison_id


def seed_multiple_prisons():
    """Seed the database with 3 dummy prisons."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Seeding database: {db_path}")
    print("Creating 3 dummy prisons for treemap demo...")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    try:
        # Clear existing locations
        print("\nClearing existing location data...")
        cursor.execute("DELETE FROM location_connections")
        cursor.execute("DELETE FROM locations")
        conn.commit()

        # Create 3 prisons
        prisons = [
            ("HMP Oakwood", 0),
            ("HMP Nottingham", 500),
            ("HMP Birmingham", 1000),
        ]

        prison_ids = []
        for prison_name, x_offset in prisons:
            prison_id = seed_prison(conn, prison_name, x_offset)
            prison_ids.append(prison_id)

        # Commit all changes
        conn.commit()
        print(f"\n✅ Successfully created {len(prisons)} prisons")
        print(f"   Total capacity: {len(prisons) * 80} prisoners")
        print(f"   Total cells: {len(prisons) * 40}")

        # Count locations by type
        cursor.execute("SELECT type, COUNT(*) FROM locations GROUP BY type ORDER BY type")
        type_counts = cursor.fetchall()
        print(f"\n📊 Location breakdown:")
        for loc_type, count in type_counts:
            print(f"   {loc_type}: {count}")

    except Exception as e:
        print(f"\n❌ Error seeding database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

    print("\n✅ Database seeding complete!")


if __name__ == "__main__":
    seed_multiple_prisons()
