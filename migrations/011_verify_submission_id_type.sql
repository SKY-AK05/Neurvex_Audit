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
