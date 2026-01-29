#!/usr/bin/env python3
"""
Apply migration 003: Add location connections table.
Run this script to add the location_connections table to the database.
"""
import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def apply_migration():
    """Apply migration 003 to add location connections table."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    migration_path = Path(__file__).parent.parent / "app" / "db" / "migrations" / "003_location_connections.sql"
    
    print(f"Applying migration to: {db_path}")
    print(f"Migration file: {migration_path}")
    
    # Read migration SQL
    with open(migration_path, 'r') as f:
        migration_sql = f.read()
    
    # Apply migration
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(migration_sql)
        conn.commit()
        print("✅ Migration 003 applied successfully!")
        
        # Verify tables exist
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='location_connections'")
        if cursor.fetchone():
            print("✅ location_connections table created")
        
        cursor.execute("PRAGMA table_info(locations)")
        columns = [row[1] for row in cursor.fetchall()]
        if 'x_coord' in columns and 'y_coord' in columns:
            print("✅ x_coord and y_coord columns added to locations table")
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    apply_migration()
