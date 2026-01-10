## Useful SQL Queries

### 1. __Overall Statistics__

```sql
-- Total inmates count
SELECT COUNT(*) as total_inmates FROM inmates;

-- Enrolled vs not enrolled
SELECT 
    COUNT(*) as total,
    SUM(is_enrolled) as enrolled,
    COUNT(*) - SUM(is_enrolled) as not_enrolled
FROM inmates;

-- Breakdown by cell block
SELECT 
    cell_block,
    COUNT(*) as total,
    SUM(is_enrolled) as enrolled,
    COUNT(*) - SUM(is_enrolled) as not_enrolled
FROM inmates
GROUP BY cell_block;
```

### 2. __Enrollment Details__

```sql
-- Total embeddings (face enrollments)
SELECT COUNT(*) as total_embeddings FROM embeddings;

-- Inmates with enrollments and their photo count
SELECT 
    i.inmate_number,
    i.first_name,
    i.last_name,
    i.cell_block,
    i.enrolled_at,
    e.model_version
FROM inmates i
JOIN embeddings e ON i.id = e.inmate_id
WHERE i.is_enrolled = 1
LIMIT 20;
```

### 3. __Failed Enrollments__

```sql
-- Inmates who failed enrollment (created but not enrolled)
SELECT 
    inmate_number,
    first_name,
    last_name,
    cell_block,
    cell_number
FROM inmates
WHERE is_enrolled = 0
ORDER BY inmate_number
LIMIT 20;
```

### 4. __Enrollment Success Rate__

```sql
-- Success rate by cell block
SELECT 
    cell_block,
    COUNT(*) as total,
    SUM(is_enrolled) as enrolled,
    ROUND(SUM(is_enrolled) * 100.0 / COUNT(*), 2) as success_rate_percent
FROM inmates
GROUP BY cell_block;
```

### 5. __Recent Enrollments__

```sql
-- Most recently enrolled inmates
SELECT 
    inmate_number,
    first_name,
    last_name,
    enrolled_at
FROM inmates
WHERE is_enrolled = 1
ORDER BY enrolled_at DESC
LIMIT 10;
```

### 6. __Search by Name__

```sql
-- Find specific inmates
SELECT 
    inmate_number,
    first_name,
    last_name,
    cell_block,
    cell_number,
    is_enrolled,
    enrolled_at
FROM inmates
WHERE first_name LIKE '%Arnold%' 
   OR last_name LIKE '%Schwarzenegger%';
```

### 7. __Database Schema__

```sql
-- View table structures
.schema inmates
.schema embeddings

-- List all tables
.tables
```

## Quick One-Liners (from bash)

```bash
# Total inmates
sqlite3 server/data/prison_rollcall.db "SELECT COUNT(*) as total_inmates FROM inmates;"

# Enrolled count
sqlite3 server/data/prison_rollcall.db "SELECT COUNT(*) as enrolled_inmates FROM inmates WHERE is_enrolled = 1;"

# Success rate
sqlite3 server/data/prison_rollcall.db "SELECT ROUND(SUM(is_enrolled) * 100.0 / COUNT(*), 2) as success_rate_percent FROM inmates;"

# Sample enrolled inmates
sqlite3 server/data/prison_rollcall.db "SELECT inmate_number, first_name, last_name FROM inmates WHERE is_enrolled = 1 LIMIT 10;"
```

