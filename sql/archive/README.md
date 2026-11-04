# SQL Archive

This directory contains SQL scripts that have been superseded by the migration system or were one-time operations.

---

## Archived Scripts

### `create_table.sql`
**Status**: Superseded by migrations  
**Original Purpose**: Initial schema creation  
**Superseded By**: Migrations 002-019 (see `../migrations/`)  
**Archived**: November 2026

The authoritative schema is now defined by the sequential migrations in the `migrations/` directory. This script is preserved for historical reference.

### `install_all.sql`
**Status**: Superseded by `scripts/migrate.py`  
**Original Purpose**: Batch migration runner  
**Superseded By**: `../scripts/migrate.py` and `../scripts/run_migration.py`  
**Archived**: November 2026

The canonical migration runner is now `scripts/migrate.py`, which provides idempotent migration execution with proper error handling.

### `fix_missing_columns.sql`
**Status**: One-time fix (likely already applied)  
**Original Purpose**: Schema repair for missing columns  
**Applied**: Pre-November 2026 (historical)  
**Archived**: November 2026

This was a one-time schema fix. The corrections have been incorporated into the proper migrations. Preserved for historical reference.

---

## Active SQL Scripts

For current SQL operations, see:

- **Migrations**: `../migrations/` - All schema changes (migrations 002-019)
- **Functions**: `../01_admin_notifications.sql`, `../02_support_requests.sql`
- **Migration Runner**: `../scripts/migrate.py`

---

## Migration System

NIWI uses sequential, idempotent SQL migrations stored in `migrations/`:

```
migrations/
├── 002_app_settings.sql
├── 003_support_email.sql
├── 004_designation.sql
├── 005_rbac.sql
├── 006_org_scoring.sql
├── 007_fix_score_columns.sql
├── 008_dynamic_forms.sql
├── 009_question_dependencies.sql
├── 010_saved_filters.sql
├── 011_verify_submission_id_type.sql
├── 012_dual_entry_invitations.sql
├── 013_organization_admins.sql
├── 014_submission_reassignments.sql
├── 015_performance_jobs_and_idempotency.sql
├── 016_service_bus_outbox.sql
├── 017_per_operation_idempotency.sql
├── 018_assessment_access_tokens.sql
├── 019_system_security_settings.sql
├── 01_remediation.sql
└── 02_features_migration.sql
```

All migrations use `IF NOT EXISTS` and `ADD COLUMN IF NOT EXISTS` patterns for idempotency.

To run migrations:
```bash
python scripts/migrate.py
```

---

**Archived**: November 4, 2026  
**Reason**: Superseded by migration system
