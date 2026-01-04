# Database Naming Conventions

## Photo Factory Database Naming Standards

### Database Names

**Format:** `{project}_{purpose}`

**Examples:**
- `photo_factory` - Main Photo Factory application database
- `photo_factory_test` - Test database (if needed)
- `photo_factory_archive` - Archive database (if needed)

### Naming Rules

1. **Use lowercase with underscores** (`snake_case`)
   - ✅ `photo_factory`
   - ❌ `PhotoFactory`, `photo-factory`, `photoFactory`

2. **Be descriptive and specific**
   - ✅ `photo_factory` (clear purpose)
   - ❌ `factory`, `main`, `app`

3. **Avoid abbreviations** (unless universally understood)
   - ✅ `photo_factory`
   - ❌ `pf`, `pf_db`

4. **Separate concerns**
   - Each service/application should have its own database
   - Photo Factory: `photo_factory`
   - Immich: Uses separate database in `immich_postgres` container

### Current Databases

**User Databases (Photo Factory):**

| Database Name | Purpose | Contains Tables | Container |
|--------------|---------|----------------|-----------|
| `photo_factory` | **Main Photo Factory application database** | `media_assets`, `system_status`, `system_status_history` | `factory_postgres` |

**System Databases (PostgreSQL):**

| Database Name | Purpose | Notes |
|--------------|---------|-------|
| `postgres` | Default PostgreSQL database | Used for PostgreSQL admin operations, not for application data |
| `template0` | PostgreSQL template database | **Read-only** template used when creating new databases. Do not modify. |
| `template1` | PostgreSQL default template | Template that new databases copy from. Can be customized (not recommended). |

**Important Notes:**
- **Only ONE user database exists:** `photo_factory`
- All Photo Factory tables are in `photo_factory`:
  - `media_assets` - Tracks all processed photos/videos
  - `system_status` - Current service heartbeats (fast lookup)
  - `system_status_history` - Historical service heartbeats (time-series)
- `template0` and `template1` are PostgreSQL system databases, not application databases
- `postgres` is the default PostgreSQL database (used for admin, not application data)

### Table Naming

**Format:** `{entity}_{type}`

**Examples:**
- `media_assets` - Media asset records
- `system_status` - Current service status (fast lookup)
- `system_status_history` - Historical service status (time-series)

### Column Naming

- Use `snake_case`
- Be descriptive: `last_heartbeat` not `lh`
- Use consistent suffixes:
  - `_at` for timestamps: `created_at`, `updated_at`
  - `_id` for foreign keys: `user_id`, `service_id`
  - `_name` for names: `service_name`, `file_name`

### Index Naming

**Format:** `idx_{table}_{columns}`

**Examples:**
- `idx_media_assets_captured_at`
- `idx_system_status_history_service_timestamp`

### Future Considerations

If adding new databases:
- `photo_factory_analytics` - For analytics/reporting
- `photo_factory_cache` - For caching layer
- `photo_factory_archive` - For archived/old data

