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
