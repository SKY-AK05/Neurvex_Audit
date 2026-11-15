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

