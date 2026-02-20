# db-inspect

Quick database inspection and health check for Prison Roll Call database.

## Description
Provides a comprehensive overview of the database state including table counts, recent records, and basic schema information.

## Steps

1. **Check database file exists**
   ```bash
   ls -lh /home/george_cairns/code/rightplace/server/data/prison_rollcall.db
   ```

2. **Get database stats (table counts)**
   ```bash
   cd /home/george_cairns/code/rightplace/server
   source .venv/bin/activate
   python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')
print('╔══════════════════════════════════════╗')
print('║     PRISON ROLL CALL DATABASE        ║')
print('╚══════════════════════════════════════╝')
print()
print('Table Counts:')
print('-' * 40)
tables = ['inmates', 'locations', 'location_connections', 'schedule_entries',
          'roll_calls', 'verifications', 'embeddings']
for table in tables:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'  {table:25} {count:>10}')
    except Exception as e:
        print(f'  {table:25} ERROR')
print()
"
   ```

3. **Show location hierarchy summary**
   ```bash
   cd /home/george_cairns/code/rightplace/server
   source .venv/bin/activate
   python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')
conn.row_factory = sqlite3.Row
print('Location Types:')
print('-' * 40)
rows = conn.execute('''
    SELECT type, COUNT(*) as count
    FROM locations
    GROUP BY type
    ORDER BY count DESC
''').fetchall()
for row in rows:
    print(f'  {row[\"type\"]:25} {row[\"count\"]:>10}')
print()
"
   ```

4. **Show recent roll calls**
   ```bash
   cd /home/george_cairns/code/rightplace/server
   source .venv/bin/activate
   python -c "
import sqlite3
from datetime import datetime
conn = sqlite3.connect('data/prison_rollcall.db')
conn.row_factory = sqlite3.Row
print('Recent Roll Calls (Last 5):')
print('-' * 40)
rows = conn.execute('''
    SELECT id, status, created_at, started_at, completed_at
    FROM roll_calls
    ORDER BY created_at DESC
    LIMIT 5
''').fetchall()
if rows:
    for row in rows:
        print(f'  ID: {row[\"id\"]} | Status: {row[\"status\"]} | Created: {row[\"created_at\"][:19]}')
else:
    print('  No roll calls found')
print()
"
   ```

5. **Show verification stats**
   ```bash
   cd /home/george_cairns/code/rightplace/server
   source .venv/bin/activate
   python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')
print('Verification Summary:')
print('-' * 40)
try:
    total = conn.execute('SELECT COUNT(*) FROM verifications').fetchone()[0]
    print(f'  Total verifications: {total}')

    # Get verification results if available
    results = conn.execute('''
        SELECT
            CASE
                WHEN match_score >= 0.7 THEN 'Match'
                WHEN match_score < 0.7 AND match_score >= 0 THEN 'No Match'
                ELSE 'Unknown'
            END as result,
            COUNT(*) as count
        FROM verifications
        GROUP BY result
    ''').fetchall()
    for row in results:
        print(f'  {row[0]:20} {row[1]:>10}')
except Exception as e:
    print(f'  Could not retrieve verification stats: {e}')
print()
"
   ```

6. **Show database size and file info**
   ```bash
   echo "Database File Info:"
   echo "----------------------------------------"
   ls -lh /home/george_cairns/code/rightplace/server/data/prison_rollcall.db | awk '{print "  Size: " $5}'
   stat -c "  Modified: %y" /home/george_cairns/code/rightplace/server/data/prison_rollcall.db | cut -d'.' -f1
   echo ""
   ```

## Success Criteria
- Database file exists and is readable
- All key tables are present
- Counts are returned without errors
- Database structure is healthy

## Output Format
Formatted ASCII table showing:
- Table row counts
- Location type distribution
- Recent roll call sessions
- Verification statistics
- Database file metadata
