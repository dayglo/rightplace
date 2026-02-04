#!/usr/bin/env python3
"""
Seed the database with the REAL HMP Oakwood structure.

Based on published sources and Inside Time reports:
- 50-acre site
- 3 residential blocks (17 buildings total)
- Capacity: 2,100-2,134 prisoners (operated by G4S)
- Community model: ~35 communities (landings) of ~60 men each
- 6 operational wings with 6 landings each = 36 communities
- Each community has 30 cells (2 per cell = 60 capacity)
- Facilities: Healthcare, Education, 2 Workshops (one football-pitch sized),
  Sports Centre, Kitchen, Visits, Drug Recovery Unit, Segregation
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

def create_connection(conn, from_id, to_id, distance=10, time=15, conn_type="corridor", bidirectional=True, escort=False):
    """Create a location connection."""
    conn_id = generate_id()
    now = datetime.utcnow().isoformat()
    
    conn.execute("""
        INSERT INTO location_connections 
        (id, from_location_id, to_location_id, distance_meters, travel_time_seconds, connection_type, is_bidirectional, requires_escort, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (conn_id, from_id, to_id, distance, time, conn_type, bidirectional, escort, now, now))

def seed_hmp_oakwood():
    """Seed the database with the real HMP Oakwood structure."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Seeding database: {db_path}")
    print("Creating HMP Oakwood (real structure)...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing locations and connections
        print("\nClearing existing data...")
        cursor.execute("DELETE FROM location_connections")
        cursor.execute("DELETE FROM locations")
        conn.commit()
        
        all_locations = {}
        
        # ===== 3 HOUSEBLOCKS =====
        # HMP Oakwood has 3 residential blocks
        print("\n📍 Creating 3 houseblocks (residential blocks)...")

        houseblocks = {}
        houseblock_configs = [
            ("Houseblock 1", 720, "Block 1", 0, 0),    # Contains A & B Wings (2 × 360)
            ("Houseblock 2", 720, "Block 2", 300, 0),  # Contains C & D Wings (2 × 360)
            ("Houseblock 3", 720, "Block 3", 600, 0),  # Contains E & F Wings (2 × 360)
        ]

        for hb_name, hb_capacity, building, x, y in houseblock_configs:
            hb_id = create_location(conn, hb_name, "houseblock",
                                   capacity=hb_capacity, building=building,
                                   x=x, y=y)
            houseblocks[building] = hb_id
            all_locations[hb_name] = hb_id
            print(f"  ✅ Created {hb_name} (capacity: {hb_capacity})")

        # ===== 6 OPERATIONAL WINGS =====
        # Each wing has 6 communities (landings) of 60 men each
        # Total: 6 wings × 360 capacity = 2,160 prisoners
        print("\n📍 Creating 6 operational wings inside houseblocks...")
        print("   (Community model: each landing is a 60-person community)")

        wings = []
        wing_configs = [
            ("A Wing", 360, "Block 1"),  # 6 communities in Houseblock 1
            ("B Wing", 360, "Block 1"),  # 6 communities in Houseblock 1
            ("C Wing", 360, "Block 2"),  # 6 communities in Houseblock 2
            ("D Wing", 360, "Block 2"),  # 6 communities in Houseblock 2
            ("E Wing", 360, "Block 3"),  # 6 communities in Houseblock 3
            ("F Wing", 360, "Block 3"),  # 6 communities in Houseblock 3
        ]

        total_communities = 0

        for idx, (wing_name, wing_capacity, building) in enumerate(wing_configs):
            # Wings are children of their houseblock
            parent_houseblock_id = houseblocks[building]
            wing_id = create_location(conn, wing_name, "wing",
                                     parent_id=parent_houseblock_id,
                                     capacity=wing_capacity, building=building,
                                     x=idx*150, y=50)
            wings.append(wing_id)
            all_locations[wing_name] = wing_id
            print(f"  ✅ Created {wing_name} (capacity: {wing_capacity}, {building})")

            # 6 landings per wing (each landing is a "community" of 60 men)
            landings = []
            cells_per_landing = 30  # 30 cells × 2 men = 60 capacity per community

            for landing_num in range(1, 7):  # 6 landings: 1-6
                landing_name = f"Landing {landing_num}"
                landing_id = create_location(conn, landing_name, "landing", parent_id=wing_id,
                                            capacity=60, floor=(landing_num-1) % 3, building=building)
                landings.append(landing_id)
                all_locations[f"{wing_name}_{landing_name}"] = landing_id
                total_communities += 1

                # Create cells on this landing
                cells = []
                wing_letter = wing_name[0]  # A, B, C, D, E, F
                for cell_num in range(1, cells_per_landing + 1):
                    cell_name = f"{wing_letter}{landing_num}-{cell_num:02d}"
                    cell_id = create_location(conn, cell_name, "cell", parent_id=landing_id,
                                             capacity=2, floor=(landing_num-1) % 3, building=building)
                    cells.append(cell_id)

                # Connect cells on same landing
                for i in range(len(cells) - 1):
                    create_connection(conn, cells[i], cells[i+1], distance=3, time=5, conn_type="corridor")

            print(f"    Created 6 communities (landings) with 30 cells each (60 men per community)")

            # Connect landings via stairwell
            for i in range(len(landings) - 1):
                create_connection(conn, landings[i], landings[i+1], distance=15, time=30, conn_type="stairwell")

        # Connect wings
        for i in range(len(wings) - 1):
            create_connection(conn, wings[i], wings[i+1], distance=80, time=120, conn_type="walkway")

        print(f"\n✅ Created 6 wings with {total_communities} total communities (landings)")
        
        # ===== SPECIAL UNITS =====
        print("\n📍 Creating special units...")
        
        healthcare_id = create_location(conn, "Healthcare Unit", "healthcare", capacity=30, building="Healthcare", x=600, y=0)
        all_locations["Healthcare"] = healthcare_id
        
        segregation_id = create_location(conn, "Segregation Unit (CSU)", "segregation", capacity=12, building="Segregation", x=600, y=50)
        all_locations["Segregation"] = segregation_id
        
        vpu_id = create_location(conn, "Vulnerable Prisoner Unit", "vpu", capacity=50, building="VPU", x=600, y=100)
        all_locations["VPU"] = vpu_id
        
        induction_id = create_location(conn, "Induction Unit", "induction", capacity=40, building="Induction", x=600, y=150)
        all_locations["Induction"] = induction_id
        
        drug_recovery_id = create_location(conn, "Drug Recovery Unit", "healthcare", capacity=25, building="Drug Recovery", x=600, y=200)
        all_locations["Drug Recovery"] = drug_recovery_id
        
        print("  ✅ Healthcare, Segregation, VPU, Induction, Drug Recovery")
        
        # ===== FACILITIES =====
        print("\n📍 Creating facilities...")
        
        education_id = create_location(conn, "Education Block", "education", capacity=150, building="Education", x=700, y=0)
        all_locations["Education"] = education_id
        
        # Two workshops - one football-pitch sized
        workshop1_id = create_location(conn, "Main Workshop (Football Pitch Size)", "workshop", capacity=120, building="Workshop 1", x=700, y=50)
        workshop2_id = create_location(conn, "Workshop 2", "workshop", capacity=80, building="Workshop 2", x=700, y=100)
        all_locations["Workshop 1"] = workshop1_id
        all_locations["Workshop 2"] = workshop2_id
        
        sports_id = create_location(conn, "Sports Centre", "gym", capacity=80, building="Sports Centre", x=700, y=150)
        all_locations["Sports Centre"] = sports_id
        
        chapel_id = create_location(conn, "Chapel / Multi-faith Room", "chapel", capacity=60, building="Chapel", x=700, y=200)
        all_locations["Chapel"] = chapel_id
        
        visits_id = create_location(conn, "Visits Building", "visits", capacity=120, building="Visits", x=800, y=0)
        all_locations["Visits"] = visits_id
        
        reception_id = create_location(conn, "Reception", "reception", capacity=25, building="Reception", x=800, y=50)
        all_locations["Reception"] = reception_id
        
        kitchen_id = create_location(conn, "Kitchen", "kitchen", capacity=40, building="Kitchen", x=800, y=100)
        all_locations["Kitchen"] = kitchen_id
        
        # Exercise yards
        yard1_id = create_location(conn, "Exercise Yard 1", "yard", capacity=150, building="Yard", x=900, y=0)
        yard2_id = create_location(conn, "Exercise Yard 2", "yard", capacity=150, building="Yard", x=900, y=100)
        all_locations["Yard 1"] = yard1_id
        all_locations["Yard 2"] = yard2_id
        
        admin_id = create_location(conn, "Admin Offices", "admin", capacity=60, building="Admin", x=900, y=150)
        all_locations["Admin"] = admin_id
        
        print("  ✅ Education, 2 Workshops, Sports Centre, Chapel, Visits, Reception, Kitchen, 2 Yards, Admin")
        
        # ===== CONNECTIONS =====
        print("\n📍 Creating connections...")
        
        # Connect wings to main facilities
        create_connection(conn, wings[0], education_id, distance=120, time=180, conn_type="walkway")
        create_connection(conn, wings[0], healthcare_id, distance=100, time=150, conn_type="walkway")
        create_connection(conn, wings[0], visits_id, distance=150, time=240, conn_type="walkway")
        create_connection(conn, wings[2], workshop1_id, distance=100, time=150, conn_type="walkway")
        
        # Connect facilities
        create_connection(conn, education_id, workshop1_id, distance=40, time=60, conn_type="corridor")
        create_connection(conn, workshop1_id, workshop2_id, distance=30, time=45, conn_type="corridor")
        create_connection(conn, workshop2_id, sports_id, distance=40, time=60, conn_type="corridor")
        create_connection(conn, sports_id, chapel_id, distance=30, time=45, conn_type="corridor")
        create_connection(conn, visits_id, reception_id, distance=25, time=40, conn_type="corridor")
        create_connection(conn, reception_id, admin_id, distance=40, time=60, conn_type="corridor")
        
        # Connect yards (with escort required)
        create_connection(conn, wings[0], yard1_id, distance=70, time=120, conn_type="gate", escort=True)
        create_connection(conn, wings[2], yard2_id, distance=70, time=120, conn_type="gate", escort=True)
        
        print("  ✅ Created facility connections")
        
        # Commit all changes
        conn.commit()
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM locations")
        location_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM location_connections")
        connection_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(capacity) FROM locations WHERE type='cell'")
        total_cell_capacity = cursor.fetchone()[0] or 0
        
        print(f"\n{'='*70}")
        print(f"✅ HMP Oakwood seeded successfully!")
        print(f"{'='*70}")
        print(f"Site: 50-acre facility")
        print(f"Total locations: {location_count}")
        print(f"Total connections: {connection_count}")
        print(f"Total cell capacity: {total_cell_capacity} prisoners")
        print(f"\nStructure:")
        print(f"  - 3 Residential Blocks (Houseblocks 1-3)")
        print(f"  - 6 Operational Wings (A-F): 360 capacity each")
        print(f"  - 36 Communities (Landings): 60 men per community")
        print(f"    • Community model: smaller, manageable groups to reduce violence")
        print(f"    • Each community has 30 cells (2 per cell)")
        print(f"  - 5 Special Units (Healthcare, Segregation, VPU, Induction, Drug Recovery)")
        print(f"  - 10 Facilities (Education, 2 Workshops, Sports Centre, Chapel,")
        print(f"                   Visits, Reception, Kitchen, 2 Yards, Admin)")
        print(f"{'='*70}")
        print(f"\nBased on published sources:")
        print(f"  - Inside Time: 2,100-2,134 capacity, community model of ~60 men")
        print(f"  - Wikipedia: 3 residential blocks, 17 buildings total, operated by G4S")
        print(f"  - Pick Everard: Healthcare, sports centre, kitchen, visits building")
        print(f"  - Prison Insider: One workshop 'the size of a football pitch'")
        print(f"{'='*70}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    seed_hmp_oakwood()
