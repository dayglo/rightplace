#!/usr/bin/env python3
"""
Generate verifications for existing rollcalls.

Creates realistic verification records with timing and status distribution.

Usage:
    cd server
    source .venv/bin/activate
    python scripts/generate_verifications.py
"""
import json
import random
import sqlite3
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# Configuration
VERIFICATION_MIN_INTERVAL = 1  # seconds between verifications
VERIFICATION_MAX_INTERVAL = 5
VERIFICATION_SUCCESS_RATE = 0.995  # 99.5% verified
VERIFICATION_MANUAL_RATE = 0.004   # 0.4% manual override
# Remaining 0.1% = not_found


def generate_id():
    """Generate a UUID."""
    return str(uuid.uuid4())


def generate_verifications():
    """Generate verifications for all rollcalls."""
    db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"
    print(f"Generating verifications for: {db_path}")

    if not db_path.exists():
        print(f"❌ Database not found: {db_path}")
        print("Run seed scripts first.")
        return

    conn = sqlite3.connect(db_path)

    try:
        # Clear existing verifications
        print("\nClearing existing verifications...")
        conn.execute("DELETE FROM verifications")
        conn.commit()

        # Get all rollcalls
        cursor = conn.execute("""
            SELECT id, name, started_at, route FROM roll_calls
            ORDER BY scheduled_at
        """)
        rollcalls = cursor.fetchall()
        print(f"Found {len(rollcalls)} rollcalls")

        total_verifications = 0

        for rollcall_id, rollcall_name, started_at, route_json in rollcalls:
            route = json.loads(route_json)
            start_dt = datetime.fromisoformat(started_at)
            current_time = start_dt

            rollcall_verifications = 0

            for stop in route:
                location_id = stop["location_id"]
                expected_inmates = stop.get("expected_inmates", [])

                for inmate_id in expected_inmates:
                    # Determine verification status
                    rand = random.random()
                    if rand < VERIFICATION_SUCCESS_RATE:
                        status = "verified"
                        confidence = round(random.uniform(0.85, 0.99), 2)
                        is_manual = 0
                    elif rand < VERIFICATION_SUCCESS_RATE + VERIFICATION_MANUAL_RATE:
                        status = "manual"
                        confidence = round(random.uniform(0.50, 0.75), 2)
                        is_manual = 1
                    else:
                        status = "not_found"
                        confidence = 0.0
                        is_manual = 0

                    verification_id = generate_id()
                    timestamp = current_time.isoformat()

                    conn.execute("""
                        INSERT INTO verifications
                        (id, roll_call_id, inmate_id, location_id, status,
                         confidence, timestamp, is_manual_override)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        verification_id, rollcall_id, inmate_id, location_id,
                        status, confidence, timestamp, is_manual
                    ))
                    total_verifications += 1
                    rollcall_verifications += 1

                    # Advance time
                    interval = random.randint(VERIFICATION_MIN_INTERVAL, VERIFICATION_MAX_INTERVAL)
                    current_time += timedelta(seconds=interval)

            # Commit after each rollcall to avoid disk I/O issues
            conn.commit()

        print(f"\n✅ Created {total_verifications} verifications")

        # Print status distribution
        cursor = conn.execute("""
            SELECT status, COUNT(*) as count,
                   ROUND(100.0 * COUNT(*) / (SELECT COUNT(*) FROM verifications), 2) as pct
            FROM verifications
            GROUP BY status
        """)
        print("\nVerification status distribution:")
        for row in cursor:
            print(f"  {row[0]}: {row[1]} ({row[2]}%)")

    except Exception as e:
        print(f"❌ Error: {e}")
        conn.rollback()
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    generate_verifications()
