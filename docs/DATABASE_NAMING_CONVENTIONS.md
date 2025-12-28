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

| Database Name | Purpose | Container | Owner |
|--------------|---------|-----------|-------|
| `photo_factory` | Main Photo Factory database (media assets, system status) | `factory_postgres` | `photo_factory` |
| `postgres` | Default PostgreSQL database (system/admin) | `factory_postgres` | `photo_factory` |
| `template0` | PostgreSQL template database (system) | `factory_postgres` | `photo_factory` |
| `template1` | PostgreSQL template database (system) | `factory_postgres` | `photo_factory` |

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

