# Photo Factory Database Structure

## Overview

**Photo Factory uses ONE user database** that contains all application tables.

## User Database

### `photo_factory` - Main Application Database

**Purpose:** Stores all Photo Factory application data

**Contains 3 tables:**

1. **`media_assets`**
   - Tracks all processed photos and videos
   - Stores file metadata, paths, dates, locations
   - Primary purpose of the Photo Factory system

2. **`system_status`**
   - Current service heartbeats (fast lookup table)
   - One row per service, updated in place
   - Used by Dashboard for real-time status

3. **`system_status_history`**
   - Historical service heartbeats (time-series table)
   - New row per heartbeat for complete history
   - Used for troubleshooting and uptime analysis

**Location:** `factory_postgres` container

## System Databases (PostgreSQL)

These are **PostgreSQL system databases**, not Photo Factory databases:

### `postgres`
- Default PostgreSQL database
- Used for PostgreSQL admin operations
- **Not used for application data**

### `template0`
- **Read-only** PostgreSQL template database
- Used as a template when creating new databases
- **DO NOT USE** - This is a PostgreSQL system database
- **DO NOT MODIFY** - It's read-only

### `template1`
- Default PostgreSQL template database
- New databases are created by copying this template
- Can be customized (not recommended)
- **DO NOT USE** - This is a PostgreSQL system database

## Summary

| Type | Database | Purpose | Contains |
|------|----------|---------|----------|
| **User** | `photo_factory` | Photo Factory application | `media_assets`, `system_status`, `system_status_history` |
| **System** | `postgres` | PostgreSQL admin | None (admin only) |
| **System** | `template0` | PostgreSQL template | PostgreSQL system (read-only) |
| **System** | `template1` | PostgreSQL template | PostgreSQL system (template) |

## Key Points

1. **Only ONE user database:** `photo_factory`
2. **All tables in one database:** We use tables, not separate databases, for different data types
3. **System databases are PostgreSQL internals:** `template0` and `template1` are not for application use
4. **Clear separation:** User data (`photo_factory`) vs. system databases (`postgres`, `template0`, `template1`)

## Why This Design?

- **Simplicity:** One database is easier to manage, backup, and restore
- **Performance:** Tables in the same database can join efficiently
- **Consistency:** All Photo Factory data in one place
- **Standard Practice:** Most applications use one database with multiple tables

## Future Considerations

If we need to separate concerns in the future, we could create:
- `photo_factory_analytics` - For analytics/reporting (separate database)
- `photo_factory_archive` - For archived data (separate database)

But for now, **one database with multiple tables is the right approach**.

