#!/usr/bin/env python3
"""
Verify name diversity in generated prisoner data.
"""
import sqlite3
from pathlib import Path
from collections import Counter

db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
conn = sqlite3.connect(db_path)

# Get random sample of names
cursor = conn.execute("""
    SELECT first_name, last_name 
    FROM inmates 
    ORDER BY RANDOM() 
    LIMIT 30
""")

print("\n" + "="*60)
print("SAMPLE OF 30 RANDOM PRISONER NAMES")
print("="*60)
for first, last in cursor.fetchall():
    print(f"  {first} {last}")

# Get name distribution
cursor = conn.execute("SELECT first_name FROM inmates")
first_names = [row[0] for row in cursor.fetchall()]
first_name_counts = Counter(first_names)

cursor = conn.execute("SELECT last_name FROM inmates")
last_names = [row[0] for row in cursor.fetchall()]
last_name_counts = Counter(last_names)

print("\n" + "="*60)
print("NAME DIVERSITY STATISTICS")
print("="*60)
print(f"Total prisoners: {len(first_names)}")
print(f"Unique first names: {len(first_name_counts)}")
print(f"Unique last names: {len(last_name_counts)}")
print(f"\nMost common first names:")
for name, count in first_name_counts.most_common(10):
    print(f"  {name}: {count}")
print(f"\nMost common last names:")
for name, count in last_name_counts.most_common(10):
    print(f"  {name}: {count}")

# Check for specific diverse names
diverse_indicators = {
    "South Asian": ["Mohammed", "Muhammad", "Ahmed", "Khan", "Patel", "Singh"],
    "Eastern European": ["Andrei", "Dmitri", "Kowalski", "Nowak", "Popov"],
    "African/Caribbean": ["Kwame", "Jamal", "Malik", "Tyrone"],
    "Middle Eastern": ["Karim", "Hassan", "Ibrahim"],
    "Latin American": ["Carlos", "Rodriguez", "Martinez", "Hernandez"],
}

print("\n" + "="*60)
print("DIVERSITY INDICATORS")
print("="*60)
for category, names in diverse_indicators.items():
    count = sum(1 for name in first_names + last_names if name in names)
    print(f"{category}: {count} occurrences")

conn.close()
print("="*60 + "\n")
