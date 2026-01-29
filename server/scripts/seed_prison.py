#!/usr/bin/env python3
"""
Seed the database with a realistic UK Category B prison.

Creates HMP Oakwood (fictional) with:
- 4 Houseblocks
- Each houseblock has 2-4 Wings
- Each wing has 3 Landings (1s, 2s, 3s)
- Each landing has 20-30 cells
- Special units (Healthcare, Segregation, VPU, Induction)
- Facilities (Education, Workshops, Gym, Chapel, Visits, Reception, Kitchen, Yards)
- Location connections for pathfinding
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

def seed_prison():
    """Seed the database with HMP Oakwood."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Seeding database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Clear existing locations and connections
        print("Clearing existing data...")
        cursor.execute("DELETE FROM location_connections")
        cursor.execute("DELETE FROM locations")
        conn.commit()
        
        print("Creating HMP Oakwood...")
        
        # Track all location IDs for connections
        all_locations = {}
        
        # ===== HOUSEBLOCKS =====
        houseblocks = []
        for hb_num in range(1, 5):  # 4 houseblocks
            hb_id = create_location(conn, f"Houseblock {hb_num}", "houseblock", 
                                   capacity=240, building=f"HB{hb_num}", x=hb_num*100, y=0)
            houseblocks.append(hb_id)
            all_locations[f"HB{hb_num}"] = hb_id
            print(f"  Created Houseblock {hb_num}")
            
            # Wings per houseblock (A, B, C, D for HB1-2, A, B for HB3-4)
            wing_letters = ['A', 'B', 'C', 'D'] if hb_num <= 2 else ['A', 'B']
            wings = []
            
            for wing_letter in wing_letters:
                wing_id = create_location(conn, f"{wing_letter} Wing", "wing", parent_id=hb_id,
                                         capacity=90, building=f"HB{hb_num}", x=hb_num*100, y=ord(wing_letter)-64)
                wings.append(wing_id)
                all_locations[f"HB{hb_num}_{wing_letter}"] = wing_id
                print(f"    Created {wing_letter} Wing")
                
                # Landings per wing (1s, 2s, 3s)
                landings = []
                for landing_num in range(1, 4):  # 3 landings
                    landing_name = f"{landing_num}s"
                    landing_id = create_location(conn, landing_name, "landing", parent_id=wing_id,
                                                capacity=30, floor=landing_num-1, building=f"HB{hb_num}")
                    landings.append(landing_id)
                    all_locations[f"HB{hb_num}_{wing_letter}_{landing_num}s"] = landing_id
                    
                    # Cells per landing
                    cells = []
                    for cell_num in range(1, 31):  # 30 cells per landing
                        cell_name = f"{wing_letter}{landing_num}-{cell_num:02d}"
                        cell_id = create_location(conn, cell_name, "cell", parent_id=landing_id,
                                                 capacity=2, floor=landing_num-1, building=f"HB{hb_num}")
                        cells.append(cell_id)
                    
                    print(f"      Created {landing_name} with 30 cells")
                    
                    # Connect cells on same landing
                    for i in range(len(cells) - 1):
                        create_connection(conn, cells[i], cells[i+1], distance=3, time=5, conn_type="corridor")
                
                # Connect landings via stairwell
                for i in range(len(landings) - 1):
                    create_connection(conn, landings[i], landings[i+1], distance=15, time=30, conn_type="stairwell")
            
            # Connect wings in same houseblock
            for i in range(len(wings) - 1):
                create_connection(conn, wings[i], wings[i+1], distance=50, time=90, conn_type="corridor")
        
        # Connect houseblocks via main walkways
        for i in range(len(houseblocks) - 1):
            create_connection(conn, houseblocks[i], houseblocks[i+1], distance=100, time=180, conn_type="walkway")
        
        print(f"\n✅ Created 4 houseblocks with wings, landings, and cells")
        
        # ===== SPECIAL UNITS =====
        print("\nCreating special units...")
        
        healthcare_id = create_location(conn, "Healthcare Unit", "healthcare", capacity=20, building="Healthcare", x=500, y=0)
        all_locations["Healthcare"] = healthcare_id
        
        segregation_id = create_location(conn, "Segregation Unit (CSU)", "segregation", capacity=10, building="Segregation", x=500, y=50)
        all_locations["Segregation"] = segregation_id
        
        vpu_id = create_location(conn, "Vulnerable Prisoner Unit", "vpu", capacity=40, building="VPU", x=500, y=100)
        all_locations["VPU"] = vpu_id
        
        induction_id = create_location(conn, "Induction Unit", "induction", capacity=30, building="Induction", x=500, y=150)
        all_locations["Induction"] = induction_id
        
        print("  ✅ Created Healthcare, Segregation, VPU, Induction")
        
        # ===== FACILITIES =====
        print("\nCreating facilities...")
        
        education_id = create_location(conn, "Education Block", "education", capacity=100, building="Education", x=600, y=0)
        all_locations["Education"] = education_id
        
        workshop_id = create_location(conn, "Workshops", "workshop", capacity=80, building="Workshops", x=600, y=50)
        all_locations["Workshops"] = workshop_id
        
        gym_id = create_location(conn, "Gymnasium", "gym", capacity=50, building="Gym", x=600, y=100)
        all_locations["Gym"] = gym_id
        
        chapel_id = create_location(conn, "Chapel", "chapel", capacity=60, building="Chapel", x=600, y=150)
        all_locations["Chapel"] = chapel_id
        
        visits_id = create_location(conn, "Visits Hall", "visits", capacity=100, building="Visits", x=700, y=0)
        all_locations["Visits"] = visits_id
        
        reception_id = create_location(conn, "Reception", "reception", capacity=20, building="Reception", x=700, y=50)
        all_locations["Reception"] = reception_id
        
        kitchen_id = create_location(conn, "Kitchen", "kitchen", capacity=30, building="Kitchen", x=700, y=100)
        all_locations["Kitchen"] = kitchen_id
        
        # Yards
        yard1_id = create_location(conn, "Exercise Yard 1", "yard", capacity=100, building="Yard", x=800, y=0)
        yard2_id = create_location(conn, "Exercise Yard 2", "yard", capacity=100, building="Yard", x=800, y=100)
        all_locations["Yard1"] = yard1_id
        all_locations["Yard2"] = yard2_id
        
        admin_id = create_location(conn, "Admin Offices", "admin", capacity=50, building="Admin", x=900, y=0)
        all_locations["Admin"] = admin_id
        
        print("  ✅ Created Education, Workshops, Gym, Chapel, Visits, Reception, Kitchen, Yards, Admin")
        
        # ===== CONNECTIONS TO FACILITIES =====
        print("\nCreating connections to facilities...")
        
        # Connect HB1 to main facilities
        create_connection(conn, houseblocks[0], education_id, distance=150, time=240, conn_type="walkway")
        create_connection(conn, houseblocks[0], healthcare_id, distance=120, time=200, conn_type="walkway")
        create_connection(conn, houseblocks[0], visits_id, distance=200, time=300, conn_type="walkway")
        
        # Connect facilities to each other
        create_connection(conn, education_id, workshop_id, distance=50, time=90, conn_type="corridor")
        create_connection(conn, workshop_id, gym_id, distance=50, time=90, conn_type="corridor")
        create_connection(conn, gym_id, chapel_id, distance=50, time=90, conn_type="corridor")
        create_connection(conn, visits_id, reception_id, distance=30, time=60, conn_type="corridor")
        create_connection(conn, reception_id, admin_id, distance=50, time=90, conn_type="corridor")
        
        # Connect yards
        create_connection(conn, houseblocks[0], yard1_id, distance=80, time=120, conn_type="gate", escort=True)
        create_connection(conn, houseblocks[2], yard2_id, distance=80, time=120, conn_type="gate", escort=True)
        
        print("  ✅ Created facility connections")
        
        # Commit all changes
        conn.commit()
        
        # Print summary
        cursor.execute("SELECT COUNT(*) FROM locations")
        location_count = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM location_connections")
        connection_count = cursor.fetchone()[0]
        
        print(f"\n{'='*60}")
        print(f"✅ HMP Oakwood seeded successfully!")
        print(f"{'='*60}")
        print(f"Total locations: {location_count}")
        print(f"Total connections: {connection_count}")
        print(f"\nStructure:")
        print(f"  - 4 Houseblocks")
        print(f"  - 10 Wings (A-D in HB1-2, A-B in HB3-4)")
        print(f"  - 30 Landings (3 per wing)")
        print(f"  - 900 Cells (30 per landing)")
        print(f"  - 4 Special Units (Healthcare, Segregation, VPU, Induction)")
        print(f"  - 9 Facilities (Education, Workshops, Gym, Chapel, Visits, Reception, Kitchen, 2 Yards, Admin)")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error seeding database: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    seed_prison()
