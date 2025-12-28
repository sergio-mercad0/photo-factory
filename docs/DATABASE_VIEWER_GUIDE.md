# Database Viewer Script - Quick Guide

## What It Is

`Stack/App_Data/view_db.ps1` is a PowerShell helper script that provides quick access to Photo Factory database information without needing to remember PostgreSQL commands.

## How to Use

**Basic command:**
```powershell
cd D:\Photo_Factory\Stack\App_Data
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 [command]
```

## Key Commands for Photo Factory

### View All Databases
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 databases
```
**Shows:**
- User databases (Photo Factory) with sizes and descriptions
- System databases (PostgreSQL) clearly marked
- Lists which tables are in `photo_factory` database

### View All Tables
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 tables
```
**Shows:** List of all tables in `photo_factory` database

### View System Status (Current)
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 status
```
**Shows:** Current service heartbeats from `system_status` table

### View System Status History
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 history
```
**Shows:** Last 20 historical heartbeat records from `system_status_history` table

### View History Statistics
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 history-count
```
**Shows:** Record counts per service, oldest/newest timestamps

### View Media Assets
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 assets-recent
```
**Shows:** 10 most recently processed files from `media_assets` table

### Interactive SQL Session
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 interactive
```
**Opens:** Full PostgreSQL interactive session for custom queries

## Quick Reference

| Command | What It Shows |
|---------|---------------|
| `databases` | All databases (user + system) with sizes |
| `tables` | All tables in photo_factory |
| `status` | Current service heartbeats |
| `history` | Last 20 historical heartbeats |
| `history-count` | History statistics per service |
| `assets-recent` | 10 most recent processed files |
| `stats` | Database statistics summary |
| `interactive` | Open psql for custom queries |

## Example Workflow

**Check what databases exist:**
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 databases
```

**See what tables are in photo_factory:**
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 tables
```

**Check if services are alive:**
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 status
```

**View recent activity:**
```powershell
powershell -ExecutionPolicy Bypass -File .\view_db.ps1 history
```

## Photo Factory Database Structure

The `photo_factory` database contains:

1. **`media_assets`** - All processed photos/videos
2. **`system_status`** - Current service heartbeats (fast lookup)
3. **`system_status_history`** - Historical heartbeats (time-series)

All three tables are in the **same database** (`photo_factory`).

