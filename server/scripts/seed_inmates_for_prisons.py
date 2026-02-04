#!/usr/bin/env python3
"""
Seed inmates into the cells created by seed_multiple_prisons.py

Creates 2 inmates per cell (matching the capacity of 2 per cell).
"""
import sqlite3
import uuid
from pathlib import Path
from datetime import date, timedelta
import random

def generate_id():
    """Generate a UUID for database records."""
    return str(uuid.uuid4())

def seed_inmates():
    """Seed inmates into cells."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Seeding inmates into database: {db_path}")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Get all cells
        cursor.execute("SELECT id, name, building FROM locations WHERE type = 'cell'")
        cells = cursor.fetchall()
        
        print(f"\nFound {len(cells)} cells")
        
        # Generate names
        first_names = [
            "James", "John", "Robert", "Michael", "William", "David", "Richard", "Joseph",
            "Thomas", "Charles", "Christopher", "Daniel", "Matthew", "Anthony", "Mark",
            "Donald", "Steven", "Paul", "Andrew", "Joshua", "Kenneth", "Kevin", "Brian",
            "George", "Edward", "Ronald", "Timothy", "Jason", "Jeffrey", "Ryan", "Jacob",
            "Gary", "Nicholas", "Eric", "Jonathan", "Stephen", "Larry", "Justin", "Scott"
        ]
        
        last_names = [
            "Smith", "Johnson", "Williams", "Brown", "Jones", "Garcia", "Miller", "Davis",
            "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Wilson", "Anderson",
            "Thomas", "Taylor", "Moore", "Jackson", "Martin", "Lee", "Thompson", "White",
            "Harris", "Sanchez", "Clark", "Ramirez", "Lewis", "Robinson", "Walker", "Young",
            "Allen", "King", "Wright", "Scott", "Torres", "Nguyen", "Hill", "Flores"
        ]
        
        # Create 2 inmates per cell
        inmate_count = 0
        for cell_id, cell_name, building in cells:
            for i in range(2):  # 2 inmates per cell
                inmate_id = generate_id()
                
                # Random name
                first_name = random.choice(first_names)
                last_name = random.choice(last_names)
                
                # Generate prisoner number (e.g., "A1234BC")
                prisoner_number = f"{random.choice('ABCDEFGH')}{random.randint(1000, 9999)}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}{random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ')}"
                
                # Random DOB (25-65 years old)
                age_years = random.randint(25, 65)
                dob = date.today() - timedelta(days=age_years * 365)
                
                # Insert inmate
                cursor.execute("""
                    INSERT INTO inmates (id, prisoner_number, first_name, last_name, dob, home_cell_id)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (inmate_id, prisoner_number, first_name, last_name, dob.isoformat(), cell_id))
                
                inmate_count += 1
        
        conn.commit()
        print(f"\n✅ Successfully created {inmate_count} inmates")
        print(f"   {inmate_count // 2} cells populated (2 inmates each)")
        
        # Verify distribution by prison
        cursor.execute("""
            SELECT 
                l_prison.name as prison,
                COUNT(i.id) as inmate_count
            FROM inmates i
            JOIN locations l_cell ON i.home_cell_id = l_cell.id
            JOIN locations l_landing ON l_cell.parent_id = l_landing.id
            JOIN locations l_wing ON l_landing.parent_id = l_wing.id
            JOIN locations l_houseblock ON l_wing.parent_id = l_houseblock.id
            JOIN locations l_prison ON l_houseblock.parent_id = l_prison.id
            WHERE l_prison.type = 'prison'
            GROUP BY l_prison.name
            ORDER BY l_prison.name
        """)
        
        print(f"\n📊 Inmate distribution by prison:")
        for prison_name, count in cursor.fetchall():
            print(f"   {prison_name}: {count} inmates")
        
    except Exception as e:
        print(f"\n❌ Error seeding inmates: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()
    
    print("\n✅ Inmate seeding complete!")

if __name__ == "__main__":
    seed_inmates()
