-- 1. UUID Migration
-- Using native gen_random_uuid() instead of uuid-ossp extension for Azure Postgres compatibility
ALTER TABLE submissions ADD COLUMN new_id UUID DEFAULT gen_random_uuid();
ALTER TABLE submissions DROP CONSTRAINT IF EXISTS submissions_pkey CASCADE;
ALTER TABLE submissions DROP COLUMN id;
ALTER TABLE submissions RENAME COLUMN new_id TO id;
ALTER TABLE submissions ADD PRIMARY KEY (id);

-- 2. GDPR Consent Columns
ALTER TABLE submissions 
ADD COLUMN IF NOT EXISTS consent_given BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS consent_timestamp TIMESTAMP;

-- 3. Dead Letter Queue
CREATE TABLE IF NOT EXISTS email_dlq (
    id SERIAL PRIMARY KEY,
    submission_id UUID NOT NULL REFERENCES submissions(id),
    payload JSONB NOT NULL,
    attempts INT DEFAULT 0,
    next_retry_at TIMESTAMP DEFAULT NOW(),
    last_error TEXT,
    status VARCHAR(20) DEFAULT 'pending'
);

-- 4. Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id SERIAL PRIMARY KEY,
    admin_id VARCHAR(255) NOT NULL,
    action_type VARCHAR(50) NOT NULL,
    target_resource_id UUID,
    old_value TEXT,
    new_value TEXT,
    ip_address VARCHAR(45),
    timestamp TIMESTAMP DEFAULT NOW()
);

-- 5. Indexes for Performance
CREATE INDEX IF NOT EXISTS idx_submissions_status ON submissions(status);
CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at ON submissions(submitted_at DESC);
CREATE INDEX IF NOT EXISTS idx_submissions_email ON submissions(email);
