#!/usr/bin/env python3
"""
Apply migration 005: Add home_cell_id to inmates table.

Run from server directory:
    python scripts/apply_migration_005.py
"""
import sqlite3
import sys
from pathlib import Path


def apply_migration(db_path: str = "data/rollcall.db"):
    """Apply migration 005 to the database."""
    migration_file = Path(__file__).parent.parent / "app/db/migrations/005_home_cell_id.sql"
    
    if not migration_file.exists():
        print(f"ERROR: Migration file not found: {migration_file}")
        sys.exit(1)
    
    # Read migration SQL
    migration_sql = migration_file.read_text()
    
    # Connect to database
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Check if column already exists
        cursor.execute("PRAGMA table_info(inmates)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if "home_cell_id" in columns:
            print("Migration already applied: home_cell_id column exists")
            return
        
        # Apply migration
        print("Applying migration 005: Add home_cell_id to inmates...")
        
        # Split and execute each statement
        for statement in migration_sql.split(";"):
            statement = statement.strip()
            if statement and not statement.startswith("--"):
                print(f"  Executing: {statement[:60]}...")
                cursor.execute(statement)
        
        conn.commit()
        print("Migration 005 applied successfully!")
        
        # Verify
        cursor.execute("PRAGMA table_info(inmates)")
        columns = [row[1] for row in cursor.fetchall()]
        print(f"Inmates table columns: {columns}")
        
    except sqlite3.Error as e:
        print(f"ERROR: {e}")
        conn.rollback()
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    db_path = sys.argv[1] if len(sys.argv) > 1 else "data/rollcall.db"
    apply_migration(db_path)
