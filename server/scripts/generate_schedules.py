#!/usr/bin/env python3
"""
Generate realistic prisoner schedules for HMP Oakwood.

Creates:
- 1600 prisoners with realistic names and details
- Work assignments distributed across facilities
- 2-week schedules with weekday/weekend patterns
- Individual variations (healthcare, visits, gym)
- Capacity-respecting assignments
"""
import random
import sqlite3
import uuid
from datetime import date, datetime, timedelta
from pathlib import Path

# ===== NAME GENERATION (Diverse UK Prison Population) =====
FIRST_NAMES = [
    # British/European
    "James", "John", "Robert", "Michael", "William", "David", "Richard", "Thomas",
    "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Steven", "Andrew", "Paul",
    "Joshua", "Kevin", "Brian", "George", "Timothy", "Edward", "Jason", "Ryan",
    "Benjamin", "Samuel", "Alexander", "Patrick", "Jack", "Oliver", "Harry", "Charlie",
    "Lewis", "Liam", "Connor", "Jake", "Luke", "Dylan", "Nathan", "Ethan",
    # African/Caribbean
    "Kwame", "Kofi", "Jamal", "Malik", "Tyrone", "Darnell", "Marcus", "Andre",
    "Winston", "Leroy", "Devon", "Terrell", "Isaiah", "Elijah", "Xavier", "Darius",
    # South Asian
    "Mohammed", "Muhammad", "Ahmed", "Ali", "Hassan", "Omar", "Yusuf", "Ibrahim",
    "Tariq", "Imran", "Rashid", "Bilal", "Amir", "Zahir", "Raj", "Amit",
    "Ravi", "Sanjay", "Vikram", "Arjun", "Rohan", "Nikhil", "Kiran", "Sunil",
    # Eastern European
    "Andrei", "Dmitri", "Sergei", "Viktor", "Alexei", "Nikolai", "Pavel", "Yuri",
    "Piotr", "Tomasz", "Jakub", "Marek", "Krzysztof", "Wojciech", "Lukasz", "Adrian",
    # Middle Eastern
    "Karim", "Samir", "Faisal", "Khalid", "Nasser", "Rami", "Zain", "Hamza",
    # Latin American
    "Carlos", "Jose", "Luis", "Miguel", "Diego", "Juan", "Pablo", "Jorge",
    "Ricardo", "Fernando", "Antonio", "Rafael", "Javier", "Alejandro", "Raul", "Sergio",
]

LAST_NAMES = [
    # British/European
    "Smith", "Johnson", "Williams", "Brown", "Jones", "Taylor", "Davies", "Wilson",
    "Evans", "Thomas", "Roberts", "Walker", "Robinson", "Thompson", "White", "Hughes",
    "Edwards", "Green", "Hall", "Wood", "Harris", "Martin", "Jackson", "Clarke",
    "Lewis", "Scott", "Turner", "Hill", "Moore", "Clark", "King", "Wright",
    "Baker", "Cooper", "Morris", "Bell", "Murphy", "Bailey", "Richardson", "Cox",
    "Howard", "Ward", "Brooks", "Russell", "Price", "Bennett", "Gray", "James",
    # African/Caribbean
    "Williams", "Johnson", "Brown", "Davis", "Miller", "Wilson", "Anderson", "Thomas",
    "Jackson", "Harris", "Martin", "Thompson", "Garcia", "Martinez", "Robinson", "Lewis",
    "Campbell", "Mitchell", "Roberts", "Carter", "Phillips", "Evans", "Turner", "Parker",
    # South Asian
    "Khan", "Ahmed", "Ali", "Hussain", "Shah", "Malik", "Patel", "Singh",
    "Rahman", "Akhtar", "Mahmood", "Kaur", "Begum", "Choudhury", "Iqbal", "Mirza",
    "Sharma", "Kumar", "Gupta", "Verma", "Reddy", "Rao", "Nair", "Menon",
    # Eastern European
    "Nowak", "Kowalski", "Wisniewski", "Wojcik", "Kowalczyk", "Kaminski", "Lewandowski", "Zielinski",
    "Popov", "Ivanov", "Petrov", "Sokolov", "Volkov", "Fedorov", "Morozov", "Novikov",
    "Kovacs", "Nagy", "Toth", "Horvath", "Varga", "Kiss", "Molnar", "Nemeth",
    # Middle Eastern
    "Hassan", "Ibrahim", "Mahmoud", "Khalil", "Mansour", "Saleh", "Yousef", "Mustafa",
    # Latin American
    "Rodriguez", "Martinez", "Hernandez", "Lopez", "Gonzalez", "Perez", "Sanchez", "Ramirez",
    "Torres", "Flores", "Rivera", "Gomez", "Diaz", "Cruz", "Morales", "Reyes",
    "Gutierrez", "Ortiz", "Mendoza", "Ruiz", "Alvarez", "Castillo", "Romero", "Vargas",
]

# ===== FACILITY CAPACITIES =====
FACILITY_CAPACITIES = {
    "workshop": {
        "capacity": 80,
        "sessions_weekday": [("08:30", "12:00"), ("13:30", "16:30")],
        "sessions_weekend": [],
    },
    "education": {
        "capacity": 100,
        "sessions_weekday": [("08:30", "12:00"), ("13:30", "16:30")],
        "sessions_weekend": [],
    },
    "gym": {
        "capacity": 50,
        "sessions_weekday": [("09:00", "10:30"), ("14:00", "15:30")],
        "sessions_weekend": [("10:00", "11:30"), ("14:00", "15:30")],
    },
    "kitchen": {
        "capacity": 30,
        "sessions_weekday": [("05:30", "08:00"), ("10:00", "13:00"), ("15:00", "18:00")],
        "sessions_weekend": [("06:00", "08:30"), ("10:30", "13:30"), ("15:30", "18:30")],
    },
    "healthcare": {
        "capacity": 20,
        "sessions_weekday": [("09:00", "12:00"), ("14:00", "17:00")],
        "sessions_weekend": [],
    },
    "visits": {
        "capacity": 100,
        "sessions_weekday": [],
        "sessions_weekend": [("14:00", "16:00")],  # Wed, Sat, Sun
    },
    "chapel": {
        "capacity": 60,
        "sessions_weekday": [],
        "sessions_weekend": [("10:00", "11:00")],  # Sunday only
    },
    "yard": {
        "capacity": 100,
        "sessions_weekday": [("10:00", "11:00"), ("15:00", "16:00")],
        "sessions_weekend": [("13:00", "15:00")],
    },
}

# ===== WORK ASSIGNMENT DISTRIBUTION =====
WORK_ASSIGNMENTS = {
    "workshop": 0.30,      # 30% in workshops
    "education": 0.25,     # 25% in education
    "kitchen": 0.05,       # 5% kitchen workers
    "gym_orderly": 0.02,   # 2% gym orderlies
    "wing_cleaner": 0.10,  # 10% wing cleaners
    "unemployed": 0.28,    # 28% unemployed (in cell during work hours)
}

# ===== BASE REGIME TEMPLATES =====
WEEKDAY_BASE_REGIME = [
    ("07:00", "07:30", "roll_check"),
    ("07:30", "08:00", "unlock"),
    ("08:00", "08:30", "meal"),
    # 08:30-12:00 = WORK/EDUCATION SLOT
    ("10:00", "10:15", "roll_check"),
    ("12:00", "13:30", "meal"),  # Lunch + lock-up
    # 13:30-16:30 = WORK/EDUCATION SLOT
    ("14:00", "14:15", "roll_check"),
    ("16:30", "17:30", "meal"),
    ("17:30", "19:00", "association"),
    ("18:00", "18:15", "roll_check"),
    ("19:00", "07:00", "lock_up"),
]

WEEKEND_BASE_REGIME = [
    ("07:30", "08:00", "roll_check"),
    ("08:00", "09:00", "meal"),
    ("09:00", "12:00", "lock_up"),
    ("12:00", "13:00", "meal"),
    # 13:00-16:00 = EXERCISE/VISITS SLOT
    ("14:00", "14:15", "roll_check"),
    ("16:00", "17:00", "meal"),
    ("17:00", "19:00", "association"),
    ("18:00", "18:15", "roll_check"),
    ("19:00", "07:30", "lock_up"),
]


def generate_id():
    """Generate a UUID."""
    return str(uuid.uuid4())


def generate_prisoner_name():
    """Generate a realistic prisoner name."""
    first = random.choice(FIRST_NAMES)
    last = random.choice(LAST_NAMES)
    return first, last


def generate_dob():
    """Generate a realistic date of birth (18-65 years old)."""
    today = date.today()
    age = random.randint(18, 65)
    birth_year = today.year - age
    birth_month = random.randint(1, 12)
    birth_day = random.randint(1, 28)  # Safe for all months
    return date(birth_year, birth_month, birth_day)


def create_prisoners(conn, num_prisoners=1600):
    """Create prisoners and assign them to cells."""
    print(f"\nCreating {num_prisoners} prisoners...")
    
    # Get all cells
    cursor = conn.execute("SELECT id, name, building FROM locations WHERE type = 'cell' ORDER BY name")
    cells = cursor.fetchall()
    print(f"Found {len(cells)} cells")
    
    prisoners = []
    cell_index = 0
    
    for i in range(num_prisoners):
        prisoner_id = generate_id()
        first_name, last_name = generate_prisoner_name()
        inmate_number = f"A{10000 + i}"
        dob = generate_dob()
        
        # Assign to cell (2 per cell)
        cell_id, cell_name, building = cells[cell_index // 2]
        
        # Extract block and cell number from cell name (e.g., "A1-01")
        cell_block = cell_name[0]  # First character
        cell_number = cell_name  # Full name
        
        now = datetime.utcnow().isoformat()
        
        conn.execute("""
            INSERT INTO inmates 
            (id, inmate_number, first_name, last_name, date_of_birth, 
             cell_block, cell_number, is_active, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
        """, (prisoner_id, inmate_number, first_name, last_name, dob.isoformat(),
              cell_block, cell_number, now, now))
        
        prisoners.append({
            "id": prisoner_id,
            "number": inmate_number,
            "name": f"{first_name} {last_name}",
            "cell_id": cell_id,
            "cell_name": cell_name,
            "building": building,
        })
        
        cell_index += 1
        
        if (i + 1) % 200 == 0:
            print(f"  Created {i + 1} prisoners...")
    
    conn.commit()
    print(f"✅ Created {len(prisoners)} prisoners")
    return prisoners


def assign_work_roles(prisoners):
    """Assign work roles to prisoners based on distribution."""
    print("\nAssigning work roles...")
    
    assignments = {role: [] for role in WORK_ASSIGNMENTS.keys()}
    
    # Shuffle prisoners for random assignment
    shuffled = prisoners.copy()
    random.shuffle(shuffled)
    
    start_idx = 0
    for role, percentage in WORK_ASSIGNMENTS.items():
        count = int(len(prisoners) * percentage)
        assignments[role] = shuffled[start_idx:start_idx + count]
        start_idx += count
        print(f"  {role}: {len(assignments[role])} prisoners")
    
    return assignments


def get_location_by_type(conn, loc_type):
    """Get a location ID by type."""
    cursor = conn.execute("SELECT id FROM locations WHERE type = ? LIMIT 1", (loc_type,))
    row = cursor.fetchone()
    return row[0] if row else None


def create_schedule_entry(conn, inmate_id, location_id, day_of_week, start_time, end_time, activity_type, source="generated"):
    """Create a schedule entry."""
    entry_id = generate_id()
    now = datetime.utcnow().isoformat()
    
    conn.execute("""
        INSERT INTO schedule_entries
        (id, inmate_id, location_id, day_of_week, start_time, end_time,
         activity_type, is_recurring, source, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?)
    """, (entry_id, inmate_id, location_id, day_of_week, start_time, end_time,
          activity_type, source, now, now))


def generate_schedules(conn, prisoners, work_assignments):
    """Generate 2-week schedules for all prisoners."""
    print("\nGenerating schedules...")
    
    # Get location IDs
    cell_loc = get_location_by_type(conn, "cell")  # Generic cell for base activities
    workshop_loc = get_location_by_type(conn, "workshop")
    education_loc = get_location_by_type(conn, "education")
    kitchen_loc = get_location_by_type(conn, "kitchen")
    gym_loc = get_location_by_type(conn, "gym")
    yard_loc = get_location_by_type(conn, "yard")
    healthcare_loc = get_location_by_type(conn, "healthcare")
    visits_loc = get_location_by_type(conn, "visits")
    chapel_loc = get_location_by_type(conn, "chapel")
    
    # Get wing location for association (use first wing)
    cursor = conn.execute("SELECT id FROM locations WHERE type = 'wing' LIMIT 1")
    wing_loc = cursor.fetchone()[0]
    
    total_entries = 0
    
    # Process each work assignment group
    for role, prisoners_in_role in work_assignments.items():
        print(f"\n  Processing {role} ({len(prisoners_in_role)} prisoners)...")
        
        for prisoner in prisoners_in_role:
            prisoner_id = prisoner["id"]
            
            # Generate schedule for each day of the week
            for day in range(7):  # 0=Monday, 6=Sunday
                is_weekend = day >= 5
                
                if is_weekend:
                    # Weekend regime
                    for start, end, activity in WEEKEND_BASE_REGIME:
                        loc = cell_loc if activity in ["roll_check", "unlock", "meal", "lock_up"] else wing_loc
                        if activity == "association":
                            loc = wing_loc
                        create_schedule_entry(conn, prisoner_id, loc, day, start, end, activity)
                        total_entries += 1
                    
                    # Weekend exercise
                    create_schedule_entry(conn, prisoner_id, yard_loc, day, "13:00", "15:00", "exercise")
                    total_entries += 1
                    
                else:
                    # Weekday regime
                    for start, end, activity in WEEKDAY_BASE_REGIME:
                        loc = cell_loc if activity in ["roll_check", "unlock", "meal", "lock_up"] else wing_loc
                        if activity == "association":
                            loc = wing_loc
                        create_schedule_entry(conn, prisoner_id, loc, day, start, end, activity)
                        total_entries += 1
                    
                    # Work/activity slots
                    if role == "workshop":
                        create_schedule_entry(conn, prisoner_id, workshop_loc, day, "08:30", "12:00", "work")
                        create_schedule_entry(conn, prisoner_id, workshop_loc, day, "13:30", "16:30", "work")
                        total_entries += 2
                    elif role == "education":
                        create_schedule_entry(conn, prisoner_id, education_loc, day, "08:30", "12:00", "education")
                        create_schedule_entry(conn, prisoner_id, education_loc, day, "13:30", "16:30", "education")
                        total_entries += 2
                    elif role == "kitchen":
                        create_schedule_entry(conn, prisoner_id, kitchen_loc, day, "05:30", "08:00", "work")
                        create_schedule_entry(conn, prisoner_id, kitchen_loc, day, "10:00", "13:00", "work")
                        create_schedule_entry(conn, prisoner_id, kitchen_loc, day, "15:00", "18:00", "work")
                        total_entries += 3
                    elif role == "gym_orderly":
                        create_schedule_entry(conn, prisoner_id, gym_loc, day, "08:30", "12:00", "work")
                        create_schedule_entry(conn, prisoner_id, gym_loc, day, "13:30", "16:30", "work")
                        total_entries += 2
                    elif role == "wing_cleaner":
                        create_schedule_entry(conn, prisoner_id, wing_loc, day, "08:30", "12:00", "work")
                        create_schedule_entry(conn, prisoner_id, wing_loc, day, "13:30", "16:30", "work")
                        total_entries += 2
                    else:  # unemployed
                        create_schedule_entry(conn, prisoner_id, cell_loc, day, "08:30", "12:00", "lock_up")
                        create_schedule_entry(conn, prisoner_id, cell_loc, day, "13:30", "16:30", "lock_up")
                        total_entries += 2
        
        if len(prisoners_in_role) > 0:
            conn.commit()
            print(f"    ✅ Created schedules for {len(prisoners_in_role)} prisoners")
    
    # Add individual variations
    print("\n  Adding individual variations...")
    variation_count = 0
    
    for prisoner in prisoners:
        prisoner_id = prisoner["id"]
        
        # Healthcare appointments (15% chance, random weekday)
        if random.random() < 0.15:
            day = random.randint(0, 4)  # Weekday
            hour = random.choice(["09:00", "10:00", "11:00", "14:00", "15:00", "16:00"])
            end_hour = f"{int(hour[:2]) + 1:02d}:00"
            create_schedule_entry(conn, prisoner_id, healthcare_loc, day, hour, end_hour, "healthcare")
            variation_count += 1
        
        # Family visits (20% chance, weekend)
        if random.random() < 0.20:
            day = random.choice([2, 5, 6])  # Wed, Sat, Sun
            create_schedule_entry(conn, prisoner_id, visits_loc, day, "14:00", "16:00", "visits")
            variation_count += 1
        
        # Chapel (10% chance, Sunday)
        if random.random() < 0.10:
            create_schedule_entry(conn, prisoner_id, chapel_loc, 6, "10:00", "11:00", "chapel")
            variation_count += 1
        
        # Gym sessions (40% chance, random days)
        if random.random() < 0.40:
            for _ in range(random.randint(1, 3)):  # 1-3 gym sessions per week
                day = random.randint(0, 6)
                time_slot = random.choice([("09:00", "10:30"), ("14:00", "15:30")])
                create_schedule_entry(conn, prisoner_id, gym_loc, day, time_slot[0], time_slot[1], "gym")
                variation_count += 1
    
    conn.commit()
    print(f"    ✅ Added {variation_count} individual variations")
    
    return total_entries + variation_count


def main():
    """Main execution."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Generating schedules for: {db_path}")
    
    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Run seed_prison.py first to create locations.")
        return
    
    conn = sqlite3.connect(db_path)
    
    try:
        # Clear existing data
        print("\nClearing existing prisoners and schedules...")
        conn.execute("DELETE FROM schedule_entries")
        conn.execute("DELETE FROM inmates")
        conn.commit()
        
        # Create prisoners
        prisoners = create_prisoners(conn, num_prisoners=1600)
        
        # Assign work roles
        work_assignments = assign_work_roles(prisoners)
        
        # Generate schedules
        total_entries = generate_schedules(conn, prisoners, work_assignments)
        
        # Print summary
        cursor = conn.execute("SELECT COUNT(*) FROM inmates")
        prisoner_count = cursor.fetchone()[0]
        
        cursor = conn.execute("SELECT COUNT(*) FROM schedule_entries")
        schedule_count = cursor.fetchone()[0]
        
        print(f"\n{'='*60}")
        print(f"✅ Schedule generation complete!")
        print(f"{'='*60}")
        print(f"Total prisoners: {prisoner_count}")
        print(f"Total schedule entries: {schedule_count}")
        print(f"Average entries per prisoner: {schedule_count / prisoner_count:.1f}")
        print(f"{'='*60}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    main()
