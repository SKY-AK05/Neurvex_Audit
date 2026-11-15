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

