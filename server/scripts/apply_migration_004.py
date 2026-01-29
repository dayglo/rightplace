#!/usr/bin/env python3
"""
Apply migration 004: Schedule Entries

Adds the schedule_entries table for prisoner timetables/regimes.
"""
import sqlite3
from pathlib import Path


def apply_migration():
    """Apply migration 004 to the database."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    migration_path = Path(__file__).parent.parent / "app" / "db" / "migrations" / "004_schedule_entries.sql"

    print(f"Applying migration 004 to: {db_path}")
    print(f"Migration file: {migration_path}")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Run setup_db.py first to create the database.")
        return

    if not migration_path.exists():
        print(f"❌ Migration file not found: {migration_path}")
        return

    # Read migration SQL
    with open(migration_path, "r") as f:
        migration_sql = f.read()

    # Apply migration
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(migration_sql)
        conn.commit()
        print("✅ Migration 004 applied successfully!")

        # Verify table was created
        cursor = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='schedule_entries'"
        )
        if cursor.fetchone():
            print("✅ schedule_entries table created")

            # Check indexes
            cursor = conn.execute(
                "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='schedule_entries'"
            )
            indexes = [row[0] for row in cursor.fetchall()]
            print(f"✅ Created {len(indexes)} indexes: {', '.join(indexes)}")
        else:
            print("❌ schedule_entries table not found after migration")

    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    apply_migration()
