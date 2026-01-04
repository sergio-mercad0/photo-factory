# PostgreSQL Direct Commands - Quick Reference

## Connecting to PostgreSQL

**From PowerShell:**
```powershell
cd D:\Photo_Factory\Stack\App_Data
docker exec -it factory_postgres psql -U photo_factory -d photo_factory
```

**One-off commands (non-interactive):**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status;"
```

## Essential Commands

### List All Databases
```sql
-- In psql:
\l

-- Or via docker:
docker exec factory_postgres psql -U photo_factory -d postgres -c "\l"
```

### List All Tables
```sql
-- In psql:
\dt

-- Or via docker:
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "\dt"
```

### Describe a Table
```sql
-- In psql:
\d table_name
\d system_status
\d media_assets
\d system_status_history

-- Or via docker:
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "\d system_status"
```

### View Current Service Status
```sql
SELECT service_name, status, last_heartbeat, current_task, updated_at 
FROM system_status 
ORDER BY service_name;
```

### View Service History (Last 20)
```sql
SELECT service_name, status, current_task, heartbeat_timestamp 
FROM system_status_history 
ORDER BY heartbeat_timestamp DESC 
LIMIT 20;
```

### View Recent Media Assets
```sql
SELECT original_name, file_hash, size_bytes, captured_at, ingested_at 
FROM media_assets 
ORDER BY ingested_at DESC 
LIMIT 10;
```

### Count Records
```sql
-- Total assets
SELECT COUNT(*) FROM media_assets;

-- History records per service
SELECT service_name, COUNT(*) as count 
FROM system_status_history 
GROUP BY service_name;

-- Total history records
SELECT COUNT(*) FROM system_status_history;
```

### Database Size
```sql
-- Size of photo_factory database
SELECT pg_size_pretty(pg_database_size('photo_factory'));

-- Size of all databases
SELECT datname, pg_size_pretty(pg_database_size(datname)) as size 
FROM pg_database 
WHERE datistemplate = false 
ORDER BY pg_database_size(datname) DESC;
```

### Table Sizes
```sql
-- Size of all tables in photo_factory
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

## Common psql Commands

| Command | Description |
|---------|-------------|
| `\l` | List all databases |
| `\dt` | List all tables |
| `\d table_name` | Describe a table |
| `\du` | List all users |
| `\q` | Quit psql |
| `\?` | Show help |
| `\c database_name` | Connect to a database |
| `\x` | Toggle expanded display (vertical output) |

## Example Workflow

**1. Connect to database:**
```powershell
docker exec -it factory_postgres psql -U photo_factory -d photo_factory
```

**2. List tables:**
```sql
\dt
```

**3. View current status:**
```sql
SELECT * FROM system_status;
```

**4. View history:**
```sql
SELECT * FROM system_status_history ORDER BY heartbeat_timestamp DESC LIMIT 10;
```

**5. Exit:**
```sql
\q
```

## One-Line Commands (No psql Session)

**View databases:**
```powershell
docker exec factory_postgres psql -U photo_factory -d postgres -c "\l"
```

**View tables:**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "\dt"
```

**View system status:**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status;"
```

**View history:**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT service_name, status, heartbeat_timestamp FROM system_status_history ORDER BY heartbeat_timestamp DESC LIMIT 10;"
```

**View recent assets:**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT original_name, ingested_at FROM media_assets ORDER BY ingested_at DESC LIMIT 10;"
```

## Formatting Output

**Better formatted output:**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -x -c "SELECT * FROM system_status;"
```
The `-x` flag shows results in expanded (vertical) format.

**CSV output:**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status;" --csv
```

**HTML output:**
```powershell
docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status;" --html
```

## Comparison: Helper Script vs Direct PostgreSQL

| Task | Helper Script | Direct PostgreSQL |
|------|---------------|-------------------|
| List databases | `.\view_db.ps1 databases` | `docker exec factory_postgres psql -U photo_factory -d postgres -c "\l"` |
| List tables | `.\view_db.ps1 tables` | `docker exec factory_postgres psql -U photo_factory -d photo_factory -c "\dt"` |
| View status | `.\view_db.ps1 status` | `docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status;"` |
| View history | `.\view_db.ps1 history` | `docker exec factory_postgres psql -U photo_factory -d photo_factory -c "SELECT * FROM system_status_history ORDER BY heartbeat_timestamp DESC LIMIT 20;"` |

**Use helper script for:** Quick, formatted output with descriptions
**Use direct PostgreSQL for:** Custom queries, automation, advanced operations

