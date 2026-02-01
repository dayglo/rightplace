# Database Access

## Production Database

- **Path**: `server/data/prison_rollcall.db`
- **Type**: SQLite 3
- **Config**: Set in `server/app/config.py` as `database_url`

## Accessing the Database

### From Python (with venv)
```bash
cd server
source .venv/bin/activate
python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')
conn.row_factory = sqlite3.Row
# Your query here
cursor = conn.execute('SELECT COUNT(*) FROM inmates')
print(cursor.fetchone()[0])
"
```

### Direct SQLite CLI
```bash
cd server
sqlite3 data/prison_rollcall.db
# Then run SQL commands:
.tables
.schema inmates
SELECT COUNT(*) FROM locations;
.quit
```

### Quick Stats Query
```bash
cd server && source .venv/bin/activate && python -c "
import sqlite3
conn = sqlite3.connect('data/prison_rollcall.db')
print('=== Database Stats ===')
for table in ['inmates', 'locations', 'schedule_entries', 'roll_calls', 'verifications']:
    try:
        count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f'{table}: {count}')
    except: pass
"
```

## Key Tables

| Table | Description |
|-------|-------------|
| `inmates` | Prisoner records with home_cell_id |
| `locations` | Location hierarchy (houseblocks, wings, cells) |
| `location_connections` | Walking distances between locations |
| `schedule_entries` | Prisoner schedules/regimes |
| `roll_calls` | Roll call records |
| `verifications` | Individual verification records |
| `embeddings` | Face embeddings for enrolled prisoners |

## Location Types

- `houseblock` - Top-level building
- `wing` - Section within houseblock
- `landing` - Floor within wing  
- `cell` - Individual cell
- Plus: `healthcare`, `education`, `workshop`, `gym`, etc.

## Example Queries

### Get all houseblocks
```sql
SELECT id, name FROM locations WHERE type = 'houseblock';
```

### Get cells under a houseblock
```sql
WITH RECURSIVE location_tree AS (
    SELECT id, name, type, parent_id FROM locations WHERE id = 'houseblock-id'
    UNION ALL
    SELECT l.id, l.name, l.type, l.parent_id 
    FROM locations l JOIN location_tree lt ON l.parent_id = lt.id
)
SELECT * FROM location_tree WHERE type = 'cell';
```

### Get prisoners in a specific cell
```sql
SELECT * FROM inmates WHERE home_cell_id = 'cell-id';
```

