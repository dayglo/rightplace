#!/usr/bin/env python3
"""
Master seed script - runs all seed scripts in order.

This script:
1. Deletes the existing database
2. Creates a fresh database with all migrations
3. Seeds locations (3 prisons with full hierarchy)
4. Seeds inmates with schedules
5. Generates rollcalls
6. Generates verifications

Usage:
    cd server
    source .venv/bin/activate
    python scripts/seed_all.py
"""
import subprocess
import sys
from pathlib import Path

# Scripts to run in order
SCRIPTS = [
    "setup_db.py",
    "seed_multiple_prisons.py",
    "generate_schedules.py",
    "generate_rollcalls.py",
    "generate_verifications.py",
]


def run_script(script_name):
    """Run a seed script."""
    script_path = Path(__file__).parent / script_name

    if not script_path.exists():
        print(f"❌ Script not found: {script_path}")
        return False

    print(f"\n{'='*60}")
    print(f"Running: {script_name}")
    print('='*60)

    result = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=Path(__file__).parent.parent,
    )

    if result.returncode != 0:
        print(f"❌ Script failed: {script_name}")
        return False

    return True


def main():
    """Run all seed scripts in order."""
    print("="*60)
    print("   PRISON ROLL CALL - FULL DATABASE SEED")
    print("="*60)

    for script in SCRIPTS:
        if not run_script(script):
            print(f"\n❌ Seed failed at: {script}")
            sys.exit(1)

    print("\n" + "="*60)
    print("   ALL SEED SCRIPTS COMPLETED SUCCESSFULLY")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
