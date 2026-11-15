-- 020_raw_submissions_and_dlq.sql
-- Dedicated raw submissions staging table and Dead Letter Queue tracking for durable ingestion

CREATE TABLE IF NOT EXISTS raw_submissions (
    submission_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    idempotency_key VARCHAR(128) NOT NULL,
    organization_id UUID,
    user_id VARCHAR(128),
    payload JSONB NOT NULL,
    schema_version INT NOT NULL DEFAULT 1,
    status VARCHAR(32) NOT NULL DEFAULT 'RECEIVED', -- 'RECEIVED', 'PENDING', 'PROCESSING', 'COMPLETED', 'RETRYING', 'FAILED', 'DEAD_LETTERED'
    scoring_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    report_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    email_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    crm_status VARCHAR(32) NOT NULL DEFAULT 'PENDING',
    retry_count INT NOT NULL DEFAULT 0,
    last_error TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_started_at TIMESTAMP WITH TIME ZONE,
    processing_completed_at TIMESTAMP WITH TIME ZONE,
    CONSTRAINT uq_raw_submissions_idempotency UNIQUE (idempotency_key)
);

-- Index for status queries and worker polling
CREATE INDEX IF NOT EXISTS idx_raw_submissions_status ON raw_submissions(status);
CREATE INDEX IF NOT EXISTS idx_raw_submissions_org ON raw_submissions(organization_id);
CREATE INDEX IF NOT EXISTS idx_raw_submissions_created_at ON raw_submissions(created_at DESC);

-- Ensure service_bus_outbox has needed fields
ALTER TABLE service_bus_outbox ADD COLUMN IF NOT EXISTS message_id VARCHAR(128);
CREATE INDEX IF NOT EXISTS idx_outbox_message_id ON service_bus_outbox (message_id);

-- Ensure submissions table references raw_submission_id if available
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS raw_submission_id UUID;
CREATE INDEX IF NOT EXISTS idx_submissions_raw_id ON submissions(raw_submission_id);

