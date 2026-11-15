# Auxiliary SQL Definitions & Support Schemas

> Unit `04-sql` · kind: feature

## Summary

DDL scripts for administrator notifications, support ticket tracking, and archive schema backups.

## Context & goal

The SQL unit maintains auxiliary SQL routines and standalone script files for secondary platform features. It defines `admin_notifications` for operational alerts, `support_requests` for respondent inquiries, and legacy archive reference scripts.

## User stories

- As a Super Admin, I receive operational system notifications for dead-letter events and queue warnings stored in `admin_notifications`.
- As a Respondent, I can submit support and accessibility inquiries stored in `support_requests` for Orchvate administrative review.

## Functional requirements

- 1. Admin Notifications Table [confirmed]: Store operational messages with notification levels (`info`, `warning`, `critical`) and read states.
- 2. Support Request Schema [confirmed]: Capture respondent inquiries with name, email, message, and created timestamps.
- 3. Archive Preservation [confirmed]: Maintain legacy SQL installation scripts in `sql/archive/` for backwards-compatibility reference.


## Interfaces & data

Interacts with `admin_notifications` and `support_requests` tables (see [DATA-MODEL.md](../../architecture/DATA-MODEL.md)).
Triggered by `POST /api/support` and system alert daemons (see [INTERFACES.md](../../architecture/INTERFACES.md)).

## Acceptance criteria

- Given a visitor submitting a support inquiry, When `POST /api/support` is called, Then a new row is inserted into `support_requests` with created timestamp.
- Given an outbox message exceeding maximum retries, When moved to dead-letter status, Then a `critical` notification is logged into `admin_notifications`.

## Edge cases & failure modes

- **Special characters or emoji in support messages:** UTF-8 encoding enforced across all text columns to prevent encoding truncation.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Consolidate standalone SQL scripts into standard numbered migration directory.
- Implement automated 180-day retention purge for resolved support tickets.


## Source material

Key source for this unit (5 file(s) total, showing up to 15):

#### `sql/01_admin_notifications.sql`

```sql
-- =============================================================================
-- Admin user notifications (bell icon in NeuroMark)
-- =============================================================================
-- When notifications_enabled = TRUE, the admin at notification_email receives
-- an email each time someone submits a new NeuroMark Audit.
--
-- Run on database: nd_audit
--   psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/01_admin_notifications.sql
-- =============================================================================

-- Settings table (single row, id = 1)
CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- Upgrade: add notification columns if table existed from an older schema
ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS notification_email VARCHAR(255) NOT NULL DEFAULT '';

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS sender_name VARCHAR(255) NOT NULL DEFAULT 'Orchvate';

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS sender_address VARCHAR(255) NOT NULL DEFAULT '';

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Ensure the single settings row exists
INSERT INTO app_settings (
    id,
    sender_name,
    sender_address,
    notification_email,
    notifications_enabled
)
VALUES (
    1,
    'Orchvate',
    '',
    'aakash.padyachi@rochvate.com',
    FALSE
)
ON CONFLICT (id) DO NOTHING;

-- Set default notification inbox if still empty (edit email below if needed)
UPDATE app_settings
SET notification_email = 'aakash.padyachi@rochvate.com'
WHERE id = 1
  AND (notification_email IS NULL OR TRIM(notification_email) = '');

COMMENT ON COLUMN app_settings.notification_email IS
    'Admin inbox: receives email when a new audit is submitted (if notifications_enabled)';

COMMENT ON COLUMN app_settings.notifications_enabled IS
    'TRUE when admin turned on bell alerts in the NeuroMark header';

```

#### `sql/02_support_requests.sql`

```sql
-- =============================================================================
-- Support requests (Support page in NeuroMark)
-- =============================================================================
-- When a user submits the support form, the message is emailed to support_email.
--
-- Requires: sql/01_admin_notifications.sql (creates app_settings table)
--
-- Run on database: nd_audit
--   psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/02_support_requests.sql
-- =============================================================================

-- Create settings table if 01 was not run yet (includes support column)
CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- Add support inbox column on existing databases
ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS support_email VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com';

-- Ensure settings row exists
INSERT INTO app_settings (id, sender_name, sender_address, support_email)
VALUES (1, 'Orchvate', '', 'aakash.padyachi@rochvate.com')
ON CONFLICT (id) DO NOTHING;

-- Set default support inbox if still empty
UPDATE app_settings
SET support_email = 'aakash.padyachi@rochvate.com'
WHERE id = 1
  AND (support_email IS NULL OR TRIM(support_email) = '');

COMMENT ON COLUMN app_settings.support_email IS
    'Inbox for Support page form submissions (NeuroMark → Support)';

```

#### `sql/archive/create_table.sql`

```sql
-- Create the nd_audit database (run as superuser on your PostgreSQL Flexible Server)
-- CREATE DATABASE nd_audit;

-- Then connect to nd_audit and run:

CREATE TABLE IF NOT EXISTS submissions (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submitted_at      TIMESTAMP DEFAULT NOW(),
    name              VARCHAR(255) NOT NULL,
    company_name      VARCHAR(255) NOT NULL,
    email             VARCHAR(255) NOT NULL,
    contact_number    VARCHAR(50),
    designation       VARCHAR(255),

    -- Gating questions (Section 4 & 8)
    has_physical_workspace VARCHAR(10),
    has_suppliers          VARCHAR(10),

    -- Raw answers Q5–Q44
    q5  VARCHAR(20), q6  VARCHAR(20), q7  VARCHAR(20), q8  VARCHAR(20), q9  VARCHAR(20),
    q10 VARCHAR(20), q11 VARCHAR(20), q12 VARCHAR(20), q13 VARCHAR(20), q14 VARCHAR(20),
    q15 VARCHAR(20), q16 VARCHAR(20), q17 VARCHAR(20), q18 VARCHAR(20), q19 VARCHAR(20),
    q20 VARCHAR(20), q21 VARCHAR(20), q22 VARCHAR(20), q23 VARCHAR(20), q24 VARCHAR(20),
    q25 VARCHAR(20), q26 VARCHAR(20), q27 VARCHAR(20), q28 VARCHAR(20), q29 VARCHAR(20),
    q30 VARCHAR(20), q31 VARCHAR(20), q32 VARCHAR(20), q33 VARCHAR(20), q34 VARCHAR(20),
    q35 VARCHAR(20), q36 VARCHAR(20), q37 VARCHAR(20), q38 VARCHAR(20), q39 VARCHAR(20),
    q40 VARCHAR(20), q41 VARCHAR(20), q42 VARCHAR(20), q43 VARCHAR(20), q44 VARCHAR(20),

    -- Section scores and levels
    lc_score DECIMAL(5,2), lc_level VARCHAR(50),
    ro_score DECIMAL(5,2), ro_level VARCHAR(50),
    we_score DECIMAL(5,2), we_level VARCHAR(50),
    be_score DECIMAL(5,2), be_level VARCHAR(50),
    tm_score DECIMAL(5,2), tm_level VARCHAR(50),
    ca_score DECIMAL(5,2), ca_level VARCHAR(50),
    pc_score DECIMAL(5,2), pc_level VARCHAR(50),
    sp_score DECIMAL(5,2), sp_level VARCHAR(50),

    -- Overall
    overall_avg   DECIMAL(4,2),
    overall_level VARCHAR(50),

    -- Email and status
    email_body    TEXT,
    status        VARCHAR(20) DEFAULT 'pending',
    sent_at       TIMESTAMP,

    -- GDPR Consent
    consent_given      BOOLEAN NOT NULL DEFAULT FALSE,
    consent_timestamp  TIMESTAMP,

    -- Organization support (multi-tenant)
    organization_id    UUID,

    -- Detailed dimension breakdown
    dimension_scores   JSONB
);

CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);

INSERT INTO app_settings (
    id, sender_name, sender_address,
    notification_email, notifications_enabled, support_email
)
VALUES (
    1, 'Orchvate', '',
    'aakash.padyachi@rochvate.com', FALSE, 'aakash.padyachi@rochvate.com'
)
ON CONFLICT (id) DO NOTHING;

-- See sql/README.md for migration scripts (notifications + support)

```

#### `sql/archive/fix_missing_columns.sql`

```sql
-- Fix Missing Columns in Submissions Table
-- Run this script to add all columns required by the backend

-- 1. Add gating question columns
ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS has_physical_workspace VARCHAR(10),
    ADD COLUMN IF NOT EXISTS has_suppliers VARCHAR(10);

-- 2. Add GDPR consent columns
ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS consent_given BOOLEAN NOT NULL DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS consent_timestamp TIMESTAMP;

-- 3. Add organization support
ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS organization_id UUID;

-- 4. Add dimension scores (detailed breakdown)
ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS dimension_scores JSONB;

-- 5. Fix score columns from INT to DECIMAL for partial scores
ALTER TABLE submissions
    ALTER COLUMN lc_score TYPE DECIMAL(5,2) USING lc_score::DECIMAL,
    ALTER COLUMN ro_score TYPE DECIMAL(5,2) USING ro_score::DECIMAL,
    ALTER COLUMN we_score TYPE DECIMAL(5,2) USING we_score::DECIMAL,
    ALTER COLUMN be_score TYPE DECIMAL(5,2) USING be_score::DECIMAL,
    ALTER COLUMN tm_score TYPE DECIMAL(5,2) USING tm_score::DECIMAL,
    ALTER COLUMN ca_score TYPE DECIMAL(5,2) USING ca_score::DECIMAL,
    ALTER COLUMN pc_score TYPE DECIMAL(5,2) USING pc_score::DECIMAL,
    ALTER COLUMN sp_score TYPE DECIMAL(5,2) USING sp_score::DECIMAL;

-- 6. Optional: Convert id from SERIAL to UUID (only if you want UUID support)
-- WARNING: This will break existing foreign key references if any exist
-- Uncomment these lines only if you need UUID support AND have no existing data
-- ALTER TABLE submissions ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
-- ALTER TABLE submissions DROP CONSTRAINT IF EXISTS submissions_pkey CASCADE;
-- ALTER TABLE submissions DROP COLUMN id;
-- ALTER TABLE submissions RENAME COLUMN new_id TO id;
-- ALTER TABLE submissions ADD PRIMARY KEY (id);

-- Verify the changes
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 'submissions'
ORDER BY ordinal_position;

```

#### `sql/archive/install_all.sql`

```sql
-- =============================================================================
-- NeuroMark Audit — full database setup (notifications + support)
-- =============================================================================
-- Run once on PostgreSQL database: nd_audit
--
--   psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/install_all.sql
--
-- Or in Azure Data Studio / pgAdmin: open this file and execute.
-- =============================================================================

-- 1) Core audit submissions table
CREATE TABLE IF NOT EXISTS submissions (
    id                SERIAL PRIMARY KEY,
    submitted_at      TIMESTAMP DEFAULT NOW(),
    name              VARCHAR(255) NOT NULL,
    company_name      VARCHAR(255) NOT NULL,
    email             VARCHAR(255) NOT NULL,
    contact_number    VARCHAR(50),

    q5  VARCHAR(20), q6  VARCHAR(20), q7  VARCHAR(20), q8  VARCHAR(20), q9  VARCHAR(20),
    q10 VARCHAR(20), q11 VARCHAR(20), q12 VARCHAR(20), q13 VARCHAR(20), q14 VARCHAR(20),
    q15 VARCHAR(20), q16 VARCHAR(20), q17 VARCHAR(20), q18 VARCHAR(20), q19 VARCHAR(20),
    q20 VARCHAR(20), q21 VARCHAR(20), q22 VARCHAR(20), q23 VARCHAR(20), q24 VARCHAR(20),
    q25 VARCHAR(20), q26 VARCHAR(20), q27 VARCHAR(20), q28 VARCHAR(20), q29 VARCHAR(20),
    q30 VARCHAR(20), q31 VARCHAR(20), q32 VARCHAR(20), q33 VARCHAR(20), q34 VARCHAR(20),
    q35 VARCHAR(20), q36 VARCHAR(20), q37 VARCHAR(20), q38 VARCHAR(20), q39 VARCHAR(20),
    q40 VARCHAR(20), q41 VARCHAR(20), q42 VARCHAR(20), q43 VARCHAR(20), q44 VARCHAR(20),

    lc_score INT,         lc_level VARCHAR(50),
    ro_score INT,         ro_level VARCHAR(50),
    we_score INT,         we_level VARCHAR(50),
    be_score INT,         be_level VARCHAR(50),
    tm_score INT,         tm_level VARCHAR(50),
    ca_score INT,         ca_level VARCHAR(50),
    pc_score INT,         pc_level VARCHAR(50),
    sp_score INT,         sp_level VARCHAR(50),

    overall_avg   DECIMAL(4,2),
    overall_level VARCHAR(50),

    email_body    TEXT,
    status        VARCHAR(20) DEFAULT 'pending',
    sent_at       TIMESTAMP
);

-- 2) App settings (email sender + admin notifications + support inbox)
CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- Safe upgrades for databases created before these columns existed
ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS sender_name VARCHAR(255) NOT NULL DEFAULT 'Orchvate';
ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS sender_address VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS notification_email VARCHAR(255) NOT NULL DEFAULT '';
ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS support_email VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com';
ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Default settings row
INSERT INTO app_settings (
    id,
    sender_name,
    sender_address,
    notification_email,
    notifications_enabled,
    support_email
)
VALUES (
    1,
    'Orchvate',
    '',
    'aakash.padyachi@rochvate.com',
    FALSE,
    'aakash.padyachi@rochvate.com'
)
ON CONFLICT (id) DO NOTHING;

-- Fill empty emails with default admin inbox
UPDATE app_settings
SET
    notification_email = 'aakash.padyachi@rochvate.com',
    support_email = 'aakash.padyachi@rochvate.com'
WHERE id = 1
  AND (
    notification_email IS NULL OR TRIM(notification_email) = ''
    OR support_email IS NULL OR TRIM(support_email) = ''
  );

```


## Improvements & refactors

- [keep-behavior] Formalize typing and input constraints for enhanced runtime validation.
- [keep-behavior] Expand automated test coverage for failure modes and timeouts.
- [keep-behavior] Optimize memory footprint and eliminate unreferenced legacy helpers.


## Definition of done

- [ ] Every functional requirement is implemented and covered by a test.
- [ ] Every acceptance-criteria scenario passes (including the failure paths).
- [ ] Every operation this unit owns in `architecture/INTERFACES.md` responds correctly.
- [ ] Every entity it writes matches `architecture/DATA-MODEL.md` (fields, types, constraints).
- [ ] Every write is satisfiable against the schema: no required (NOT NULL, no-default) column or foreign key is left unfilled; anonymous/public operations write only to anonymous-capable entities (no owner FK).
- [ ] Every enum/domain value this unit uses is one of the members fully enumerated in `architecture/DATA-MODEL.md`.
- [ ] Every edge case & failure mode above is handled.
- [ ] `node scripts/analyze.mjs --check --out <out>` passes — no unresolved agent callouts or placeholders, and every reference resolves.

