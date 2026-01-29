#!/usr/bin/env python3
"""
Export audit logs to CSV.

Usage:
    python export_audit.py                          # Export last 7 days
    python export_audit.py --days 30                # Export last 30 days
    python export_audit.py --start 2025-01-01 --end 2025-01-31  # Date range
    python export_audit.py --output audit_2025.csv  # Custom output file
"""
import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path to import app modules
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.db.repositories.audit_repo import AuditRepository
from app.services.audit_service import AuditService


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Export audit logs to CSV")

    parser.add_argument(
        "--days",
        type=int,
        help="Number of days to export (from today backwards)",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--output",
        type=str,
        default="audit_export.csv",
        help="Output CSV file path (default: audit_export.csv)",
    )
    parser.add_argument(
        "--db",
        type=str,
        help="Database file path (default: data/prison_rollcall.db)",
    )

    return parser.parse_args()


def main():
    """Export audit logs to CSV."""
    args = parse_args()

    # Determine database path
    if args.db:
        db_path = Path(args.db)
    else:
        db_path = Path(__file__).parent.parent / "data" / "prison_rollcall.db"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}", file=sys.stderr)
        sys.exit(1)

    # Determine time range
    end = datetime.now()

    if args.start and args.end:
        # Use explicit date range
        try:
            start = datetime.fromisoformat(args.start)
            end = datetime.fromisoformat(args.end)
        except ValueError as e:
            print(f"Error: Invalid date format: {e}", file=sys.stderr)
            print("Use YYYY-MM-DD format", file=sys.stderr)
            sys.exit(1)
    elif args.days:
        # Use days backwards from now
        start = end - timedelta(days=args.days)
    else:
        # Default: last 7 days
        start = end - timedelta(days=7)

    # Connect to database
    print(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    try:
        # Create service
        audit_repo = AuditRepository(conn)
        audit_service = AuditService(audit_repo)

        # Export logs
        print(f"Exporting audit logs from {start.date()} to {end.date()}")
        csv_content = audit_service.export_logs(start, end, format="csv")

        # Write to file
        output_path = Path(args.output)
        output_path.write_text(csv_content)

        # Count entries
        line_count = len(csv_content.strip().split("\n")) - 1  # Subtract header

        print(f"✓ Exported {line_count} audit entries to {output_path}")
        print(f"  Time range: {start.isoformat()} to {end.isoformat()}")

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
