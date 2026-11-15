-- 017_per_operation_idempotency.sql
-- Durable Per-Operation Idempotency Ledger and Status Accuracy Tracking

-- 1. Create durable per-operation processing state ledger table
CREATE TABLE IF NOT EXISTS submission_operation_states (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    submission_id UUID NOT NULL REFERENCES submissions(id) ON DELETE CASCADE,
    operation_type VARCHAR(64) NOT NULL, -- 'REPORT_GENERATION', 'EMAIL_DELIVERY', 'CRM_SYNC', 'ADMIN_NOTIFICATION'
    status VARCHAR(32) NOT NULL DEFAULT 'PENDING', -- 'PENDING', 'PROCESSING', 'COMPLETED', 'SKIPPED', 'FAILED'
    idempotency_key VARCHAR(128) NOT NULL,
    attempts INT NOT NULL DEFAULT 0,
    max_attempts INT NOT NULL DEFAULT 3,
    locked_at TIMESTAMP WITH TIME ZONE,
    locked_by VARCHAR(128),
    last_error TEXT,
    result_metadata JSONB DEFAULT '{}'::jsonb,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    CONSTRAINT uq_sub_op_idempotency UNIQUE (idempotency_key),
    CONSTRAINT uq_sub_op_type UNIQUE (submission_id, operation_type)
);

-- Partial index for active lock management and stranded crash recovery
CREATE INDEX IF NOT EXISTS idx_sub_op_lookup 
ON submission_operation_states (submission_id, operation_type);

CREATE INDEX IF NOT EXISTS idx_sub_op_status 
ON submission_operation_states (status);

-- 2. Add granular reporting and HubSpot traceability columns to submissions table
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS report_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS admin_notify_status VARCHAR(32) DEFAULT 'PENDING';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS hubspot_deal_id VARCHAR(64);
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS hubspot_contact_id VARCHAR(64);

CREATE INDEX IF NOT EXISTS idx_submissions_report_status 
ON submissions (report_status);

