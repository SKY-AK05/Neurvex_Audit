-- 022_performance_indexes.sql
-- High-performance partial indexes and composite sorting indexes for instant dashboard loads and queue draining

-- 1. High-speed partial index for raw submissions active queue (drains pending/processing queue in < 1ms)
CREATE INDEX IF NOT EXISTS idx_raw_submissions_pending_queue 
ON raw_submissions (created_at ASC) 
WHERE status IN ('RECEIVED', 'PROCESSING');

-- 2. High-speed partial index for service bus outbox active queue
CREATE INDEX IF NOT EXISTS idx_outbox_pending_queue 
ON service_bus_outbox (created_at ASC) 
WHERE status IN ('PENDING', 'FAILED');

-- 3. Composite index on submissions for instant pagination and sorting without filesort
CREATE INDEX IF NOT EXISTS idx_submissions_submitted_at_id 
ON submissions (submitted_at DESC NULLS LAST, id DESC);

-- 4. Fast index for raw_submissions status filtering
CREATE INDEX IF NOT EXISTS idx_raw_submissions_active_status 
ON raw_submissions (status) 
WHERE status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING');
