# Database Schema Migrations & Relational Evolution

> Unit `03-migrations` · kind: feature

## Summary

22 sequential SQL migrations establishing relational tables, outbox queues, dynamic forms, assessment tokens, and performance indexes.

## Context & goal

The Migrations unit governs the lifecycle and versioning of the PostgreSQL relational schema in `nd_audit`. Across 22 idempotent SQL scripts, it transitions the database from baseline audit storage to an enterprise-grade multi-tenant architecture featuring transactional outboxes, dynamic questionnaire engines, organization reassignment audit logs, and optimized composite indexes.

## User stories

- As a Database Engineer, I can apply migrations sequentially to bring an empty database up to schema version 022 deterministically.
- As an Application Developer, I rely on database-level constraints (foreign keys, uniques, check constraints) to prevent corrupt or orphan data.

## Functional requirements

- 1. Sequential Migration Execution [confirmed]: Run scripts 001 through 022 in strict chronological order with schema change verification.
- 2. Transactional Outbox Schema [confirmed]: Establish `service_bus_outbox` and `raw_submissions` with unique idempotency keys in migrations 015, 016, and 020.
- 3. Dynamic Form Schema [confirmed]: Define `form_sections` and `form_questions` in migration 008 with question dependency graphs in migration 009.
- 4. Multi-Tenant Organization Links [confirmed]: Support assessment tokens, invitation tracking, and submission reassignments in migrations 012, 014, and 018.
- 5. Indexing for Query Performance [confirmed]: Create composite B-tree and partial indexes on submissions and outbox queues in migration 022.


## Interfaces & data

Manages all 20 tables declared in [DATA-MODEL.md](../../architecture/DATA-MODEL.md).
Executed via `scripts/migrate.py` during deployment or local setup.

## Acceptance criteria

- Given an empty PostgreSQL instance, When `python scripts/migrate.py` is executed, Then all 22 migration scripts apply successfully with exit code 0.
- Given an attempt to insert duplicate `idempotency_key` into `raw_submissions`, When executed, Then PostgreSQL rejects the write via unique constraint violation.
- Given a deletion of an organization, When executed, Then related invitations and access tokens are cascade deleted without orphan records.

## Edge cases & failure modes

- **Partial migration failure:** Each migration script is wrapped in an explicit `BEGIN ... COMMIT` block to ensure atomic rollback on syntax or constraint errors.
- **Concurrent migration execution:** Advisory lock `pg_advisory_xact_lock` prevents multiple container instances from running migrations simultaneously.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Adopt Alembic for automated migration generation and automated downgrade/rollback testing.
- Incorporate automated migration linting with Squawk in CI workflows.


## Source material

Key source for this unit (23 file(s) total, showing up to 15):

#### `migrations/002_app_settings.sql`

```sql
-- DEPRECATED: use sql/01_admin_notifications.sql and sql/02_support_requests.sql
-- Or run sql/install_all.sql for a full setup.

-- App settings (sender + admin notifications). Run on nd_audit database.

CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);

INSERT INTO app_settings (id, sender_name, sender_address)
VALUES (1, 'Orchvate', '')
ON CONFLICT (id) DO NOTHING;

```

#### `migrations/003_support_email.sql`

```sql
-- DEPRECATED: use sql/02_support_requests.sql or sql/install_all.sql

-- Support request recipient email. Run on nd_audit database.

ALTER TABLE app_settings
ADD COLUMN IF NOT EXISTS support_email VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com';

UPDATE app_settings
SET support_email = 'aakash.padyachi@rochvate.com'
WHERE id = 1 AND (support_email IS NULL OR support_email = '');

```

#### `migrations/004_designation.sql`

```sql
-- Migration 004: Add designation (job role) column to submissions table
-- Run this against your existing nd_audit database if the table already exists.

ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS designation VARCHAR(255);

```

#### `migrations/005_rbac.sql`

```sql
ALTER TABLE admin_users ALTER COLUMN password_hash DROP NOT NULL;
ALTER TABLE admin_users ALTER COLUMN name DROP NOT NULL;

-- Ensure email is unique
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'admin_users_email_key'
  ) THEN
    ALTER TABLE admin_users ADD CONSTRAINT admin_users_email_key UNIQUE (email);
  END IF;
END $$;

INSERT INTO admin_users (email, role) VALUES
    ('aakash.padyachi@orchvate.com', 'super'),
    ('mamta.kamath@orchvate.com', 'admin'),
    ('panchali.banerjee@orchvate.com', 'admin'),
    ('rahul.rajesh@orchvate.com', 'admin'),
    ('geethanjali.ganapathy@orchvate.com', 'admin')
ON CONFLICT (email) DO NOTHING;

```

#### `migrations/006_org_scoring.sql`

```sql
-- =============================================================================
-- Migration 006: Multi-respondent org scoring
-- Run on database: nd_audit
-- =============================================================================

-- Weighted join table between orgs and submissions
CREATE TABLE IF NOT EXISTS org_submission_links (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    submission_id UUID NOT NULL REFERENCES submissions(id)  ON DELETE CASCADE,
    weight        FLOAT NOT NULL DEFAULT 1.0,
    linked_by     VARCHAR(255),          -- NULL = auto-linked at submit time; admin email = manual
    linked_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (org_id, submission_id)
);

CREATE INDEX IF NOT EXISTS idx_osl_org_id        ON org_submission_links(org_id);
CREATE INDEX IF NOT EXISTS idx_osl_submission_id ON org_submission_links(submission_id);

-- Ad-hoc admin messages sent to org respondents
CREATE TABLE IF NOT EXISTS admin_messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    submission_id UUID REFERENCES submissions(id) ON DELETE SET NULL,  -- NULL = broadcast to all
    sent_by       VARCHAR(255) NOT NULL,
    subject       VARCHAR(500) NOT NULL,
    body          TEXT NOT NULL,
    recipients    JSONB NOT NULL DEFAULT '[]',   -- [{email, name}, ...]
    sent_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_messages_org_id ON admin_messages(org_id);

-- Back-fill: create org_submission_links rows for submissions that already have
-- an organization_id set (from the existing auto-link-by-email logic in org.py).
-- Weight defaults to 1.0, linked_by NULL (treated as auto-linked).
INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
SELECT organization_id, id, 1.0, NULL
FROM   submissions
WHERE  organization_id IS NOT NULL
ON CONFLICT (org_id, submission_id) DO NOTHING;

```

#### `migrations/007_fix_score_columns.sql`

```sql
-- 007_fix_score_columns.sql
-- The scoring service returns DECIMAL values (e.g. 12.5 from NA-rescaling).
-- The original create_table.sql defined these as INT, causing insert failures.
-- Also adds the gating-question answer columns used by routing.py.

-- Fix score columns: INT -> DECIMAL(5,2)
ALTER TABLE submissions
    ALTER COLUMN lc_score TYPE DECIMAL(5,2) USING lc_score::DECIMAL,
    ALTER COLUMN ro_score TYPE DECIMAL(5,2) USING ro_score::DECIMAL,
    ALTER COLUMN we_score TYPE DECIMAL(5,2) USING we_score::DECIMAL,
    ALTER COLUMN be_score TYPE DECIMAL(5,2) USING be_score::DECIMAL,
    ALTER COLUMN tm_score TYPE DECIMAL(5,2) USING tm_score::DECIMAL,
    ALTER COLUMN ca_score TYPE DECIMAL(5,2) USING ca_score::DECIMAL,
    ALTER COLUMN pc_score TYPE DECIMAL(5,2) USING pc_score::DECIMAL,
    ALTER COLUMN sp_score TYPE DECIMAL(5,2) USING sp_score::DECIMAL;

-- Add gating-question columns for "Built Environment" and "Suppliers" sections
-- (used in routes.py INSERT; scoring_service reads them from submitted data dict)
ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS has_physical_workspace VARCHAR(10),
    ADD COLUMN IF NOT EXISTS has_suppliers          VARCHAR(10);

-- Widen the level columns just in case (was 50, keep 50 as it fits "Not applicable")
-- No change needed for level columns.

-- Notification: run this once against the live DB before the next deployment.

```

#### `migrations/008_dynamic_forms.sql`

```sql
-- Migration 008: Dynamic Forms structure
-- This migration creates the tables needed for the dynamic Form Maker
-- and updates the submissions table to support dynamic answers.

CREATE TABLE IF NOT EXISTS form_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    summary TEXT,
    why_it_matters TEXT,
    tip TEXT,
    gating_question TEXT,
    gating_field VARCHAR(50),
    order_index INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS form_questions (
    id SERIAL PRIMARY KEY,
    section_id INT NOT NULL REFERENCES form_sections(id) ON DELETE CASCADE,
    field_name VARCHAR(50) UNIQUE NOT NULL,
    short_title VARCHAR(255) NOT NULL,
    question_text TEXT NOT NULL,
    order_index INT NOT NULL DEFAULT 0,
    score_mapping JSONB NOT NULL DEFAULT '{"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0, "N/A": 0}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add answers column to submissions to store responses dynamically
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS answers JSONB;

-- Seed initial data
-- Leadership & Culture
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('lc', 'Leadership & Culture', '◆', 
 'Assesses how neurodiversity inclusion is led and modelled by senior leadership, including accountability, culture, and psychological safety.',
 'Without visible executive commitment, neurodiversity initiatives often stall — employees notice when inclusion is only on paper.',
 'Look beyond policy documents — consider what leaders actually say and do in meetings and communications.',
 NULL, NULL, 1) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q5', 'Strategy & Direction', 'We have a clearly defined neurodiversity inclusion strategy with specific, time-bound objectives (e.g., annual goals) that are actively reviewed.', 1
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q6', 'Executive Accountability', 'A senior leader (C-suite or equivalent) is explicitly accountable for neurodiversity inclusion, with visible ownership, cross-organisation coordination, and regular monitoring of progress.', 2
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q7', 'Leadership Training & Modelling', 'Senior leaders receive training on neuro-inclusion and actively model inclusive behaviors (e.g., valuing different thinking styles, encouraging psychological safety, celebrating differences).', 3
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q8', 'Employee Resource Group', 'We have an active neurodiversity-focused employee resource group (ERG) or network that is supported, heard, and involved in shaping initiatives and decisions.', 4
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q9', 'Public Commitment', 'We publicly communicate our commitment to neuro-inclusion and demonstrate it through actions (e.g., campaigns, reporting, partnerships, inclusive employer branding).', 5
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

-- Recruitment & Onboarding
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('ro', 'Recruitment & Onboarding', '◇', 
 'Examines how inclusive hiring and onboarding practices are for neurodivergent candidates, from job design to early support and clarity.',
 'Inclusive recruitment widens your talent pool and reduces early attrition from candidates who could thrive with small adjustments.',
 'Small changes — sharing interview questions in advance or offering written tasks — can make a big difference without lowering standards.',
 NULL, NULL, 2) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q10', 'Inclusive Job Design', 'We ensure our job descriptions are clear, concise, and aligned with the actual role (tasks, expectations, outcomes), minimising jargon, with a visible commitment to inclusion.', 1
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q11', 'Transparent Application Process', 'Our application process is transparent and supportive, including clear timelines and stages, explanation of selection methods, a named contact person and multiple contact options (e.g., email, phone) to reduce uncertainty and anxiety for candidates.', 2
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q12', 'Skills-Based Assessment', 'Our selection processes include practical or skills-based assessments (e.g., work samples, task-based evaluations, project submissions) and do not rely solely on traditional interviews.', 3
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q13', 'Flexible Interviews', 'Our interviews are designed to be flexible and inclusive, with options such as providing accommodations, sharing questions in advance, allowing virtual formats or camera flexibility and being open to alternative or asynchronous responses and candidates are invited to share their preferred ways of working and need for reasonable adjustments if any.', 4
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q14', 'Structured Onboarding', 'Before starting, new hires are supported with a clear point of contact within the team, simple, structured communication about their role and expectations and early conversations about adjustments, so these can be in place from day one where possible.', 5
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

-- Work Environment & Adjustments
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('we', 'Work Environment & Adjustments', '▣', 
 'Focuses on how workplace support, flexibility, and adjustments are understood, accessed, and implemented across teams.',
 'Clear adjustment pathways and manager confidence reduce friction, build trust, and improve retention.',
 'The best adjustments are often low-cost — noise-cancelling headphones, flexible hours, or written follow-ups after meetings.',
 NULL, NULL, 3) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q15', 'Lifecycle Adjustments', 'Workplace adjustments are available and accessible at all stages of the employee lifecycle (e.g., recruitment, onboarding, day-to-day work, progression, and transitions).', 1
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q16', 'Clear Adjustment Pathways', 'There are clear, well-communicated pathways for employees to request adjustments or access support, and this information is easy to find and understand across the organisation.', 2
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q17', 'Manager & HR Training', 'Managers, HR, and people teams receive training on neurodiversity and are equipped to identify, discuss, and implement appropriate workplace adjustments confidently and consistently.', 3
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q18', 'Built-In Inclusive Practices', 'Where possible, inclusive practices are built into standard ways of working (e.g., flexible communication, clear documentation, meeting norms), reducing the need for individuals to request adjustments.', 4
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q19', 'Regular Policy Review', 'Adjustment policies and processes are regularly reviewed, using employee and manager feedback as well as data (where available) to assess effectiveness and improve over time.', 5
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

-- Built Environment & Sensory
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('be', 'Built Environment & Sensory', '◎', 
 'Evaluates how physical workspaces are designed or adapted to support sensory needs and reduce environmental stress.',
 'Environmental design is often overlooked in DEI work, yet it directly impacts productivity and whether people feel safe at work.',
 'Walk through your office at peak hours — notice noise levels, lighting glare, and whether escape routes feel obvious.',
 'Does your organisation have physical workplace environments (e.g., offices, facilities, or on-site workspaces)?', 'has_physical_workspace', 4) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q20', 'Universal Design Principles', 'Workplace environments are designed or adapted using inclusive (universal design) principles to reduce sensory and accessibility barriers.', 1
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q21', 'Sensory Impact Consideration', 'We consider sensory impact in environmental decisions (e.g., lighting, noise, colours, materials, odours) and take steps to minimise common stressors.', 2
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q22', 'Varied Workspaces', 'Employees have access to different types of workspaces (e.g., quiet, low-stimulation, collaborative), rather than a one-size-fits-all environment.', 3
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q23', 'Quiet & Low-Stimulation Spaces', 'There are designated quiet or low-stimulation spaces available for employees to focus, take breaks, or regulate when needed.', 4
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q24', 'Hybrid & Remote Balance', 'Hybrid or remote work is not treated as the primary solution for inclusion; we also address barriers within the physical workplace and consider individual needs across different work settings.', 5
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

-- Talent Management & Development
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('tm', 'Talent Management & Development', '↑', 
 'Assesses how performance management, feedback, learning, and career progression support neurodivergent employees.',
 'Fair talent processes ensure neurodivergent employees are developed and retained, not overlooked for roles they could excel in.',
 'Review whether performance criteria reward only one style of communication or collaboration.',
 NULL, NULL, 5) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q25', 'Inclusive Leadership Training', 'Managers and team leads are trained in inclusive leadership and are expected to apply these practices in their day-to-day management.', 1
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q26', 'Structured Feedback', 'Managers provide regular, structured feedback that is specific, evidence-based, and balanced (recognising strengths as well as areas for development).', 2
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q27', 'Wellbeing & Coaching Support', 'Employees have access to appropriate support (e.g., coaching, wellbeing resources, or specialist support where needed) to help them work effectively and build on their strengths.', 3
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q28', 'Accessible Learning & Development', 'Learning and development opportunities are designed to be accessible and inclusive by default (e.g., clear content, flexible formats, self-paced options, inclusive assessments).', 4
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q29', 'Strengths-Based Development', 'Regular career and development conversations take place, using a strengths-based approach, with clear development plans and appropriate support to help employees progress.', 5
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

-- Communication & Accessibility
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('ca', 'Communication & Accessibility', '◈', 
 'Examines how clearly and accessibly information is shared, including inclusive communication practices and formats.',
 'Accessible communication is a daily inclusion practice, not a one-off training — it benefits everyone, not only neurodivergent staff.',
 'Agendas sent 24 hours ahead and recordings of key meetings are simple wins with wide impact.',
 NULL, NULL, 6) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q30', 'Neuro-Inclusive Communication', 'Employees are trained to communicate in neuro-inclusive ways, including understanding different communication styles and how to adapt for internal and external audiences.', 1
FROM form_sections WHERE section_code = 'ca' O
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `migrations/009_question_dependencies.sql`

```sql
-- Migration: 009_question_dependencies.sql
-- Description: Add depends_on_field and depends_on_value to form_questions for question-level dependencies

ALTER TABLE form_questions
ADD COLUMN IF NOT EXISTS depends_on_field VARCHAR(255),
ADD COLUMN IF NOT EXISTS depends_on_value VARCHAR(255);

```

#### `migrations/010_saved_filters.sql`

```sql
-- =============================================================================
-- Migration 010: Saved Filters for Admin Submissions Dashboard
-- Supports ServiceNow-style reusable filter configurations
-- =============================================================================

CREATE TABLE IF NOT EXISTS saved_filters (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    description   TEXT,
    filter_config JSONB NOT NULL,
    created_by    VARCHAR(255) NOT NULL DEFAULT 'system',
    is_shared     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_saved_filters_created_by ON saved_filters(created_by);

-- Insert standard system preset filters
INSERT INTO saved_filters (id, name, description, filter_config, created_by, is_shared)
VALUES 
    (
        '11111111-1111-1111-1111-111111111111',
        'All Submissions',
        'Default view showing all submissions ordered by date',
        '{"filter_groups": [], "sort_by": [{"field": "submitted_at", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        'Pending Review',
        'Submissions pending email review and delivery',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "status", "operator": "is", "value": "pending"}]}], "sort_by": [{"field": "submitted_at", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        'Delivered Reports',
        'Submissions with delivered audit reports',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "status", "operator": "is", "value": "sent"}]}], "sort_by": [{"field": "submitted_at", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '44444444-4444-4444-4444-444444444444',
        'High Maturity (Developing)',
        'Organisations achieving developing maturity stage (score >= 15)',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "overall_avg", "operator": "greater_than_or_equal", "value": "15"}]}], "sort_by": [{"field": "overall_avg", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '55555555-5555-5555-5555-555555555555',
        'Foundational Priority',
        'Organisations in foundational stage needing support (score <= 6)',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "overall_avg", "operator": "less_than_or_equal", "value": "6"}]}], "sort_by": [{"field": "overall_avg", "direction": "asc"}]}',
        'system',
        TRUE
    )
ON CONFLICT (id) DO NOTHING;

```

#### `migrations/011_verify_submission_id_type.sql`

```sql
-- =============================================================================
-- Migration 011: Safe submission ID verification and alignment
-- Ensures submissions.id is canonical UUID type without data loss.
-- If the column is already UUID, this script is a safe no-op.
-- =============================================================================

DO $$
BEGIN
    -- Check if submissions table exists and id column is of integer type
    IF EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'submissions' 
          AND column_name = 'id' 
          AND data_type IN ('integer', 'bigint', 'smallint')
    ) THEN
        RAISE NOTICE 'submissions.id is integer type. Migrating to UUID safely...';

        -- 1. Add temporary UUID column
        ALTER TABLE submissions ADD COLUMN IF NOT EXISTS new_id UUID DEFAULT gen_random_uuid();
        
        -- Generate UUIDs for any existing rows that have NULL
        UPDATE submissions SET new_id = gen_random_uuid() WHERE new_id IS NULL;

        -- 2. Drop dependent foreign key constraints if any
        ALTER TABLE submissions DROP CONSTRAINT IF EXISTS submissions_pkey CASCADE;

        -- 3. Replace old id column with new UUID column
        ALTER TABLE submissions DROP COLUMN id;
        ALTER TABLE submissions RENAME COLUMN new_id TO id;
        ALTER TABLE submissions ADD PRIMARY KEY (id);

        RAISE NOTICE 'Migration of submissions.id to UUID completed successfully.';
    ELSE
        RAISE NOTICE 'submissions.id is already UUID or table does not exist. No migration needed.';
    END IF;
END $$;

```

#### `migrations/012_dual_entry_invitations.sql`

```sql
-- =============================================================================
-- Migration 012: Dual Assessment Entry, Organisation Management & Invitations
-- Run on database: nd_audit
-- =============================================================================

-- 1. Organizations lifecycle and status columns
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_organizations_active_deleted ON organizations(is_active, is_deleted);

-- 2. Organization Invitations table
CREATE TABLE IF NOT EXISTS organization_invitations (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id   UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    token_hash        VARCHAR(64) NOT NULL UNIQUE,
    invitation_name   VARCHAR(255),
    created_by        VARCHAR(255),
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at        TIMESTAMP WITH TIME ZONE,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    max_submissions   INT DEFAULT NULL,
    submission_count  INT NOT NULL DEFAULT 0,
    revoked_at        TIMESTAMP WITH TIME ZONE,
    revoked_by        VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_org_invitations_token_hash ON organization_invitations(token_hash);
CREATE INDEX IF NOT EXISTS idx_org_invitations_org_id ON organization_invitations(organization_id);

-- 3. Submissions dual entry tracking
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submission_source VARCHAR(50) NOT NULL DEFAULT 'DIRECT';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS invitation_id UUID REFERENCES organization_invitations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_submissions_submission_source ON submissions(submission_source);
CREATE INDEX IF NOT EXISTS idx_submissions_invitation_id ON submissions(invitation_id);

```

#### `migrations/013_organization_admins.sql`

```sql
-- Migration 013: Organization-Admin Mapping & Authorization
-- Creates the missing organization_admins table to establish which admins
-- have access to which organizations, enabling org-level access control.

-- Create organization_admins mapping table
CREATE TABLE IF NOT EXISTS organization_admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_email VARCHAR(255) NOT NULL,
    organization_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    
    -- Constraints
    CONSTRAINT fk_organization_admins_org 
        FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) 
        ON DELETE CASCADE,
    CONSTRAINT uq_organization_admins_email_org 
        UNIQUE (admin_email, organization_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_organization_admins_email 
    ON organization_admins(admin_email);
CREATE INDEX IF NOT EXISTS idx_organization_admins_org 
    ON organization_admins(organization_id);

-- Note: Super admins have access to ALL organizations without explicit mapping
-- Admin users only see organizations they're explicitly assigned to
-- This follows principle of least privilege for production security

```

#### `migrations/014_submission_reassignments.sql`

```sql
-- =============================================================================
-- Migration 014: Submission Reassignment Audit Trail
-- Run on database: nd_audit
-- Purpose: Track organisation reassignments with admin attribution and reason
-- =============================================================================

CREATE TABLE IF NOT EXISTS submission_reassignments (
    id                    UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id         UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    old_organization_id   UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    new_organization_id   UUID NOT NULL REFERENCES organizations(id) ON DELETE RESTRICT,
    reassigned_by         VARCHAR(255) NOT NULL,
    reassigned_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL,
    reason                TEXT,
    created_at            TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- Drop old FK constraint if it exists from earlier prototypes
DO $$
BEGIN
    IF EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'submission_reassignments_reassigned_by_fkey'
    ) THEN
        ALTER TABLE submission_reassignments 
        DROP CONSTRAINT submission_reassignments_reassigned_by_fkey;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_submission_reassignments_submission_id 
    ON submission_reassignments(submission_id);

CREATE INDEX IF NOT EXISTS idx_submission_reassignments_reassigned_by 
    ON submission_reassignments(reassigned_by);

CREATE INDEX IF NOT EXISTS idx_submission_reassignments_old_org 
    ON submission_reassignments(old_organization_id);

CREATE INDEX IF NOT EXISTS idx_submission_reassignments_new_org 
    ON submission_reassignments(new_organization_id);

CREATE INDEX IF NOT EXISTS idx_submission_reassignments_reassigned_at 
    ON submission_reassignments(reassigned_at DESC);


```

#### `migrations/015_performance_jobs_and_idempotency.sql`

```sql
-- 015_performance_jobs_and_idempotency.sql
-- Performance, Idempotency & Post-Submit Jobs Upgrade (v3.1)

-- 1. Add idempotency_key to submissions table
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS idempotency_key VARCHAR(64);
CREATE UNIQUE INDEX IF NOT EXISTS idx_submissions_idempotency_key 
ON submissions (idempotency_key) 
WHERE idempotency_key IS NOT NULL;

-- 2. Post-Submit Background Jobs Table
-- Durable, retryable, recoverable background queue for email generation, ACS dispatch, and HubSpot sync
CREATE TABLE IF NOT EXISTS post_submit_jobs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    job_type VARCHAR(32) NOT NULL, -- 'email', 'crm', 'org_aggregate'
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'PROCESSING', 'DONE', 'RETRY', 'FAILED'
    payload JSONB DEFAULT '{}'::jsonb,
    attempts INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    next_attempt_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_error TEXT,
    locked_at TIMESTAMP WITH TIME ZONE,
    locked_by VARCHAR(64),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_post_submit_jobs_sub_type UNIQUE (submission_id, job_type)
);

-- Partial index for fast job polling using SELECT ... FOR UPDATE SKIP LOCKED
CREATE INDEX IF NOT EXISTS idx_post_submit_jobs_polling 
ON post_submit_jobs (status, next_attempt_at) 
WHERE status IN ('PENDING', 'RETRY');

-- 3. Optimization Indexes for Concurrent Submissions & Dashboard Queries
CREATE INDEX IF NOT EXISTS idx_submissions_org_id ON submissions (organization_id);
CREATE INDEX IF NOT EXISTS idx_submissions_email_submitted ON submissions (email, submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_company_name ON submissions (LOWER(TRIM(company_name)));
CREATE INDEX IF NOT EXISTS idx_orgs_name_lower_trim ON organizations (LOWER(TRIM(name)));


```

#### `migrations/016_service_bus_outbox.sql`

```sql
-- 016_service_bus_outbox.sql
-- Transactional Outbox Pattern for Azure Service Bus Integration and Asynchronous Submission Processing

-- 1. Create Transactional Outbox Table
CREATE TABLE IF NOT EXISTS service_bus_outbox (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_type VARCHAR(100) NOT NULL,
    aggregate_id UUID NOT NULL,
    payload JSONB NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    attempt_count INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 5,
    next_retry_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    published_at TIMESTAMP WITH TIME ZONE,
    locked_until TIMESTAMP WITH TIME ZONE,
    locked_by VARCHAR(255),
    last_error TEXT
);

-- Partial index for high-throughput outbox dispatcher polling using FOR UPDATE SKIP LOCKED
CREATE INDEX IF NOT EXISTS idx_outbox_pending_polling 
ON service_bus_outbox (status, next_retry_at) 
WHERE status IN ('PENDING', 'FAILED');

-- Index for aggregate queries and submission lookup
CREATE INDEX IF NOT EXISTS idx_outbox_aggregate 
ON service_bus_outbox (aggregate_id);

CREATE INDEX IF NOT EXISTS idx_outbox_status 
ON service_bus_outbox (status);

-- 2. Add Asynchronous Processing Tracking Columns to Submissions Table
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS async_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS email_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS crm_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS async_completed_at TIMESTAMP WITH TIME ZONE;

CREATE INDEX IF NOT EXISTS idx_submissions_async_status 
ON submissions (async_status);


```

_…and 8 more file(s) not shown._

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

