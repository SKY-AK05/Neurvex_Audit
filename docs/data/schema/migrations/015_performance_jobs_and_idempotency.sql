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

