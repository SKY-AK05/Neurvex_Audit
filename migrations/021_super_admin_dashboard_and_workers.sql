-- 021_super_admin_dashboard_and_workers.sql
-- Super Admin Dashboard cached snapshot, worker fleet tracking, and performance indexes

-- 1. One-row dashboard snapshot table for multi-server cached statistics
CREATE TABLE IF NOT EXISTS dashboard_snapshot (
    id INTEGER PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    data JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 2. Worker heartbeat and fleet tracking table
CREATE TABLE IF NOT EXISTS workers (
    worker_id VARCHAR(128) PRIMARY KEY,
    worker_type VARCHAR(64) NOT NULL DEFAULT 'service_bus_worker',
    status VARCHAR(32) NOT NULL DEFAULT 'idle', -- 'active', 'idle', 'offline'
    current_task VARCHAR(255),
    jobs_completed INT NOT NULL DEFAULT 0,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    last_heartbeat TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_workers_heartbeat ON workers(last_heartbeat);
CREATE INDEX IF NOT EXISTS idx_workers_status ON workers(status);

-- 3. Add worker_id to raw_submissions and ensure all performance indexes exist
ALTER TABLE raw_submissions ADD COLUMN IF NOT EXISTS worker_id VARCHAR(128);

CREATE INDEX IF NOT EXISTS idx_raw_submissions_status ON raw_submissions(status);
CREATE INDEX IF NOT EXISTS idx_raw_submissions_created_at ON raw_submissions(created_at);
CREATE INDEX IF NOT EXISTS idx_raw_submissions_worker_id ON raw_submissions(worker_id);
