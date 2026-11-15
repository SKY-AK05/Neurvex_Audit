# Data model

| Setting | Value |
| --- | --- |
| Mode | `preserve` |
| Level | `complex` |
| Fidelity | `embed` |
| Generated with | `reconstruct@2.29.16` |

The Neuro-Inclusive Workplace Index (NIWI) persistence layer is built on PostgreSQL 14+ across 22 incremental SQL migrations. It enforces relational integrity, concurrency isolation (`SELECT FOR UPDATE SKIP LOCKED`), audit trails, and strict data partitioning between sensitive raw survey inputs and aggregated benchmark analytics.

## Schema / model source files

- `app/api/routes.py`
- `app/models/__init__.py`
- `app/models/audit.py`
- `app/models/form_builder.py`
- `app/models/user.py`
- `app/services/settings_service.py`
- `migrations/002_app_settings.sql`
- `migrations/003_support_email.sql`
- `migrations/004_designation.sql`
- `migrations/005_rbac.sql`
- `migrations/006_org_scoring.sql`
- `migrations/007_fix_score_columns.sql`
- `migrations/008_dynamic_forms.sql`
- `migrations/009_question_dependencies.sql`
- `migrations/010_saved_filters.sql`
- `migrations/011_verify_submission_id_type.sql`
- `migrations/012_dual_entry_invitations.sql`
- `migrations/013_organization_admins.sql`
- `migrations/014_submission_reassignments.sql`
- `migrations/015_performance_jobs_and_idempotency.sql`
- `migrations/016_service_bus_outbox.sql`
- `migrations/017_per_operation_idempotency.sql`
- `migrations/018_assessment_access_tokens.sql`
- `migrations/019_system_security_settings.sql`
- `migrations/01_remediation.sql`
- `migrations/020_raw_submissions_and_dlq.sql`
- `migrations/021_super_admin_dashboard_and_workers.sql`
- `migrations/022_performance_indexes.sql`
- `migrations/02_features_migration.sql`
- `scripts/migrate.py`
- `scripts/setup_db.py`
- `sql/01_admin_notifications.sql`
- `sql/02_support_requests.sql`
- `sql/archive/create_table.sql`
- `sql/archive/fix_missing_columns.sql`
- `sql/archive/install_all.sql`

## Entities

| Entity / Table | Field | Type | Constraints | Relation |
| --- | --- | --- | --- | --- |
| `organizations` | `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | 1:N with invitations, tokens, links |
| `organizations` | `name` | VARCHAR(255) | NOT NULL, UNIQUE | Referenced across submissions and links |
| `organizations` | `slug` | VARCHAR(255) | UNIQUE, INDEX | URL identifier |
| `organizations` | `domain` | VARCHAR(255) | NULLABLE | Corporate email domain validation |
| `organizations` | `is_active` | BOOLEAN | DEFAULT TRUE | Soft active flag |
| `organizations` | `is_deleted` | BOOLEAN | DEFAULT FALSE | Soft delete flag |
| `organizations` | `approval_status` | VARCHAR(32) | NOT NULL, DEFAULT 'approved' | Enum: pending, approved, rejected, suspended |
| `organizations` | `created_at` | TIMESTAMPTZ | DEFAULT NOW() | System timestamp |
| `organizations` | `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | System timestamp |
| `admin_users` | `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | 1:N with admin_sessions |
| `admin_users` | `email` | VARCHAR(255) | NOT NULL, UNIQUE, INDEX | Entra ID corporate identity match |
| `admin_users` | `role` | VARCHAR(32) | NOT NULL, DEFAULT 'admin' | Enum: admin, super |
| `admin_users` | `is_active` | BOOLEAN | DEFAULT TRUE | Authorization gate |
| `admin_users` | `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Creation audit |
| `admin_sessions` | `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Belong to admin_users |
| `admin_sessions` | `user_id` | UUID | NOT NULL, REFERENCES admin_users(id) ON DELETE CASCADE | Foreign Key |
| `admin_sessions` | `session_token` | VARCHAR(255) | NOT NULL, UNIQUE | Active session lookup |
| `admin_sessions` | `expires_at` | TIMESTAMPTZ | NOT NULL | Expiration timestamp |
| `form_sections` | `id` | INTEGER | PRIMARY KEY GENERATED ALWAYS AS IDENTITY | 1:N with form_questions |
| `form_sections` | `title` | VARCHAR(255) | NOT NULL | Section display title |
| `form_sections` | `slug` | VARCHAR(100) | NOT NULL, UNIQUE | Pillar identifier (e.g. physical_environment) |
| `form_sections` | `display_order` | INTEGER | NOT NULL, DEFAULT 0 | Ordering index in questionnaire |
| `form_sections` | `is_active` | BOOLEAN | DEFAULT TRUE | Dynamic form visibility |
| `form_questions` | `id` | INTEGER | PRIMARY KEY GENERATED ALWAYS AS IDENTITY | Belongs to form_sections |
| `form_questions` | `section_id` | INTEGER | NOT NULL, REFERENCES form_sections(id) ON DELETE CASCADE | Foreign Key |
| `form_questions` | `question_text` | TEXT | NOT NULL | Questionnaire prompt string |
| `form_questions` | `question_type` | VARCHAR(32) | NOT NULL, DEFAULT 'likert_5' | Enum: likert_5, text, single_choice |
| `form_questions` | `order_index` | INTEGER | NOT NULL, DEFAULT 0 | Question order within section |
| `form_questions` | `is_required` | BOOLEAN | DEFAULT TRUE | Validation requirement |
| `raw_submissions` | `submission_id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Staging table for 202 Ingestion |
| `raw_submissions` | `payload` | JSONB | NOT NULL | Complete verbatim survey responses |
| `raw_submissions` | `idempotency_key` | VARCHAR(255) | NOT NULL, UNIQUE | Enforces single ingestion attempt |
| `raw_submissions` | `status` | VARCHAR(32) | NOT NULL, DEFAULT 'pending' | Enum: pending, claimed, processed, failed |
| `raw_submissions` | `created_at` | TIMESTAMPTZ | DEFAULT NOW(), INDEX | Submission timestamp |
| `service_bus_outbox` | `id` | BIGSERIAL | PRIMARY KEY | Concurrency queue table |
| `service_bus_outbox` | `submission_id` | UUID | NOT NULL, REFERENCES raw_submissions(submission_id) ON DELETE CASCADE | Foreign Key |
| `service_bus_outbox` | `topic` | VARCHAR(100) | NOT NULL, DEFAULT 'niwi.survey.completed' | Event topic |
| `service_bus_outbox` | `payload` | JSONB | NOT NULL | Event message payload |
| `service_bus_outbox` | `status` | VARCHAR(32) | NOT NULL, DEFAULT 'pending', INDEX | Enum: pending, processing, completed, failed |
| `service_bus_outbox` | `retry_count` | INTEGER | NOT NULL, DEFAULT 0 | Worker retry attempts (max 3) |
| `service_bus_outbox` | `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Staging timestamp |
| `service_bus_outbox` | `processed_at` | TIMESTAMPTZ | NULLABLE | Processing finish timestamp |
| `submission_operation_states` | `id` | BIGSERIAL | PRIMARY KEY | Operation tracker |
| `submission_operation_states` | `submission_id` | UUID | NOT NULL | Audit submission UUID |
| `submission_operation_states` | `operation_type` | VARCHAR(64) | NOT NULL | Enum: score_calculation, email_dispatch, hubspot_sync |
| `submission_operation_states` | `status` | VARCHAR(32) | NOT NULL, DEFAULT 'pending' | Enum: pending, completed, failed |
| `submission_operation_states` | `attempts` | INTEGER | NOT NULL, DEFAULT 0 | Operation attempts |
| `submission_operation_states` | `last_error` | TEXT | NULLABLE | Exception traceback on failure |
| `submissions` | `id` | UUID | PRIMARY KEY | Persisted scored survey record |
| `submissions` | `organisation_name`| VARCHAR(255) | NOT NULL, INDEX | Employer name |
| `submissions` | `designation` | VARCHAR(255) | NULLABLE | Respondent professional role |
| `submissions` | `department` | VARCHAR(255) | NULLABLE | Respondent department |
| `submissions` | `respondent_email` | VARCHAR(255) | NULLABLE, INDEX | Respondent contact (omitted if anonymous) |
| `submissions` | `score_total` | INTEGER | NOT NULL | Aggregated inclusion score (0–160) |
| `submissions` | `score_physical_env` | INTEGER | NOT NULL | Pillar 1 score (0–20) |
| `submissions` | `score_hiring` | INTEGER | NOT NULL | Pillar 2 score (0–20) |
| `submissions` | `score_culture` | INTEGER | NOT NULL | Pillar 3 score (0–20) |
| `submissions` | `score_policies` | INTEGER | NOT NULL | Pillar 4 score (0–20) |
| `submissions` | `score_career` | INTEGER | NOT NULL | Pillar 5 score (0–20) |
| `submissions` | `score_communication`| INTEGER | NOT NULL | Pillar 6 score (0–20) |
| `submissions` | `score_daily_ops` | INTEGER | NOT NULL | Pillar 7 score (0–20) |
| `submissions` | `score_wellbeing` | INTEGER | NOT NULL | Pillar 8 score (0–20) |
| `submissions` | `maturity_tier` | VARCHAR(32) | NOT NULL | Foundational, Early Progress, Developing, Proficient, Leading |
| `submissions` | `responses` | JSONB | NOT NULL | Itemized question answers |
| `submissions` | `submitted_at` | TIMESTAMPTZ | DEFAULT NOW(), INDEX | Submission timestamp |
| `draft_submissions` | `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | In-progress survey responses |
| `draft_submissions` | `resume_token` | VARCHAR(255) | NOT NULL, UNIQUE, INDEX | Client resumption token |
| `draft_submissions` | `email` | VARCHAR(255) | NULLABLE | Optional draft owner email |
| `draft_submissions` | `org_id` | UUID | NULLABLE, REFERENCES organizations(id) ON DELETE SET NULL | Associated organization |
| `draft_submissions` | `form_data` | JSONB | NOT NULL | Serialized partial responses |
| `draft_submissions` | `current_step` | INTEGER | DEFAULT 1 | Stepper index |
| `draft_submissions` | `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Auto-save timestamp |
| `org_submission_links`| `id` | BIGSERIAL | PRIMARY KEY | Many-to-many relationship |
| `org_submission_links`| `org_id` | UUID | NOT NULL, REFERENCES organizations(id) ON DELETE CASCADE | Associated organization |
| `org_submission_links`| `submission_id` | UUID | NOT NULL, REFERENCES submissions(id) ON DELETE CASCADE | Associated submission |
| `org_submission_links`| `linked_at` | TIMESTAMPTZ | DEFAULT NOW() | Linkage timestamp |
| `organization_invitations` | `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Invite tracking |
| `organization_invitations` | `org_id` | UUID | NOT NULL, REFERENCES organizations(id) ON DELETE CASCADE | Inviting organization |
| `organization_invitations` | `token` | VARCHAR(255) | NOT NULL, UNIQUE, INDEX | Unique URL invitation code |
| `organization_invitations` | `invitee_email` | VARCHAR(255) | NULLABLE | Targeted invitee email |
| `organization_invitations` | `status` | VARCHAR(32) | NOT NULL, DEFAULT 'active' | Enum: active, used, expired, revoked |
| `organization_invitations` | `expires_at` | TIMESTAMPTZ | NOT NULL | Expiry threshold |
| `assessment_access_tokens` | `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Campaign access tokens |
| `assessment_access_tokens` | `org_id` | UUID | NOT NULL, REFERENCES organizations(id) ON DELETE CASCADE | Bound organization |
| `assessment_access_tokens` | `token` | VARCHAR(255) | NOT NULL, UNIQUE, INDEX | Campaign access token string |
| `assessment_access_tokens` | `max_uses` | INTEGER | NULLABLE | Quota limit (NULL for unlimited) |
| `assessment_access_tokens` | `use_count` | INTEGER | NOT NULL, DEFAULT 0 | Count of completed audits |
| `assessment_access_tokens` | `status` | VARCHAR(32) | NOT NULL, DEFAULT 'active' | Enum: active, inactive, exhausted |
| `submission_reassignments`| `id` | BIGSERIAL | PRIMARY KEY | Audit re-attribution log |
| `submission_reassignments`| `submission_id` | UUID | NOT NULL, REFERENCES submissions(id) ON DELETE CASCADE | Target submission |
| `submission_reassignments`| `previous_org_name`| VARCHAR(255) | NOT NULL | Source organization |
| `submission_reassignments`| `new_org_name` | VARCHAR(255) | NOT NULL | Destination organization |
| `submission_reassignments`| `reassigned_by` | VARCHAR(255) | NOT NULL | Admin email who authorized |
| `submission_reassignments`| `reassigned_at` | TIMESTAMPTZ | DEFAULT NOW() | Reassignment timestamp |
| `saved_filters` | `id` | UUID | PRIMARY KEY, DEFAULT gen_random_uuid() | Custom admin filter sets |
| `saved_filters` | `name` | VARCHAR(255) | NOT NULL | Name of filter preset |
| `saved_filters` | `filter_criteria` | JSONB | NOT NULL | Query filters JSON |
| `saved_filters` | `created_by` | VARCHAR(255) | NOT NULL | Admin email |
| `admin_notifications` | `id` | BIGSERIAL | PRIMARY KEY | Operational notification bell |
| `admin_notifications` | `message` | TEXT | NOT NULL | Alert text |
| `admin_notifications` | `level` | VARCHAR(32) | NOT NULL, DEFAULT 'info' | Enum: info, warning, critical |
| `admin_notifications` | `is_read` | BOOLEAN | DEFAULT FALSE | Read state |
| `admin_notifications` | `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Alert timestamp |
| `support_requests` | `id` | BIGSERIAL | PRIMARY KEY | In-app support tickets |
| `support_requests` | `name` | VARCHAR(255) | NOT NULL | Requester contact name |
| `support_requests` | `email` | VARCHAR(255) | NOT NULL | Requester email |
| `support_requests` | `message` | TEXT | NOT NULL | Support inquiry description |
| `support_requests` | `created_at` | TIMESTAMPTZ | DEFAULT NOW() | Request timestamp |
| `system_security_settings`| `key` | VARCHAR(100) | PRIMARY KEY | Configuration key |
| `system_security_settings`| `value` | JSONB | NOT NULL | Dynamic parameter value |
| `system_security_settings`| `updated_at` | TIMESTAMPTZ | DEFAULT NOW() | Update timestamp |
| `app_settings` | `key` | VARCHAR(100) | PRIMARY KEY | Application setting key |
| `app_settings` | `value` | TEXT | NOT NULL | Value string |

## Relations & integrity

1. **Transactional Outbox Decoupling:**
   - Ingestion writes atomically to `raw_submissions` and `service_bus_outbox` in a single database transaction.
   - If writing fails, both records rollback completely; no partial submissions can occur.
   - Workers query `service_bus_outbox` using `SELECT ... FOR UPDATE SKIP LOCKED` guaranteeing that concurrent background threads never process the same message simultaneously.

2. **Foreign Key Cascades & Soft Deletion:**
   - Soft deletion on `organizations` via `is_deleted = TRUE` preserves historical audit submission linkage for benchmark analytics.
   - Direct deletions on `organizations` cascade to child tokens, invitations, and link records (`ON DELETE CASCADE`).
   - Deleting an admin user cascades to clear active session tokens (`ON DELETE CASCADE`).

3. **Performance Indexes (Migration 022):**
   - B-tree index on `submissions(organisation_name, submitted_at DESC)` for fast analytics aggregation.
   - Unique hash index on `raw_submissions(idempotency_key)` to prevent duplicate submissions.
   - Partial index on `service_bus_outbox(status)` WHERE `status IN ('pending', 'failed')` for efficient outbox worker polling.

## Enums & domain types

### 1. `approval_status` (Organization lifecycle)
- `pending`: Registered organization awaiting administrative validation.
- `approved`: Active organization fully eligible for survey link generation and public verification.
- `rejected`: Application denied by administrator.
- `suspended`: Access temporarily revoked.

### 2. `user_role` (RBAC access level)
- `admin`: Standard Administrator. Global read access, organization dashboard management, report generation, and invitation link creation.
- `super`: Super Administrator. Full system control including user creation/deletion, system settings, destructive purges, and dead-letter queue replay.

### 3. `submission_status` (Survey ingestion state)
- `pending`: Acknowledged via HTTP 202; staged in `raw_submissions` and `service_bus_outbox`.
- `claimed`: Outbox worker has acquired transaction lock (`SKIP LOCKED`).
- `completed`: Scored, persisted into `submissions`, and email delivered.
- `failed`: Background calculation or email failed; pending retry (up to 3 attempts).
- `dead_lettered`: Retries exhausted; manual administrative intervention required.

### 4. `invitation_status` (Invite token lifecycle)
- `active`: Valid and available for respondent participation.
- `used`: Single-use invitation successfully submitted.
- `expired`: Beyond expiration threshold (`expires_at < NOW()`).
- `revoked`: Cancelled manually by organization administrator.

### 5. `inclusion_pillars` (8 Assessment Dimensions)
1. `physical_environment`: Sensory workplace accessibility, noise cancellation, lighting, quiet zones.
2. `hiring_recruitment`: Neuro-inclusive interview formats, explicit task descriptions, unbiased evaluation.
3. `culture_leadership`: Executive championship, open psychological safety, stigma eradication.
4. `policies_practices`: Formal accommodation pathways, flexible working arrangements, remote options.
5. `career_development`: Fair performance appraisal, transparent promotion criteria, mentorship.
6. `communication`: Multi-modal communication tools, clear asynchronous written expectations.
7. `daily_operations`: Meeting structures, agenda dissemination, focused uninterrupted deep work time.
8. `wellbeing_support`: Employee Resource Groups (ERGs), specialized mental health benefits, coaching.

### 6. `maturity_tiers` (5 Progression Levels)
- `Foundational` (Score 0–39): Minimal accommodations; baseline legal compliance; high sensory/cultural friction.
- `Early Progress` (Score 40–79): Ad-hoc support; isolated champions; emerging awareness without enterprise policies.
- `Developing` (Score 80–119): Standardized inclusion policies; documented accommodation request procedures.
- `Proficient` (Score 120–139): Widespread cultural integration; active executive sponsorship; structured feedback loops.
- `Leading` (Score 140–160): Best-in-class industry benchmark; systemic neuro-inclusion embedded in all operations.
