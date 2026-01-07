#!/usr/bin/env python3
"""
Database Setup Script - Prison Roll Call

This script:
- Deletes the existing database
- Creates a fresh database with all migrations
- Useful for development and testing

Usage:
    cd server
    source venv/bin/activate
    python scripts/setup_db.py
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.config import Settings
from app.db.database import get_connection, init_db


def main():
    settings = Settings()
    db_path = Path(settings.database_url)
    
    # Delete existing database
    if db_path.exists():
        print(f"🗑️  Deleting existing database: {db_path}")
        db_path.unlink()
        print("✅ Database deleted")
    else:
        print(f"ℹ️  No existing database found at {db_path}")
    
    # Create fresh database
    print(f"\n📦 Creating fresh database: {db_path}")
    conn = get_connection(settings.database_url)
    
    print("📋 Running migrations...")
    init_db(conn)
    
    print("✅ Database initialized successfully!")
    print("\n📊 Database ready at:", db_path)
    
    conn.close()


if __name__ == "__main__":
    main()
