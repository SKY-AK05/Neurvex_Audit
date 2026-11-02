-- =============================================================================
-- Migration 012: Dual Assessment Entry, Organisation Management & Invitations
-- Run on database: nd_audit
-- =============================================================================

-- 1. Organizations lifecycle and status columns
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_active BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN NOT NULL DEFAULT FALSE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS updated_by VARCHAR(255);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_at TIMESTAMP WITH TIME ZONE;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS deleted_by VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_organizations_active_deleted ON organizations(is_active, is_deleted);

-- 2. Organization Invitations table
CREATE TABLE IF NOT EXISTS organization_invitations (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id   UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    token_hash        VARCHAR(64) NOT NULL UNIQUE,
    invitation_name   VARCHAR(255),
    created_by        VARCHAR(255),
    created_at        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    expires_at        TIMESTAMP WITH TIME ZONE,
    is_active         BOOLEAN NOT NULL DEFAULT TRUE,
    max_submissions   INT DEFAULT NULL,
    submission_count  INT NOT NULL DEFAULT 0,
    revoked_at        TIMESTAMP WITH TIME ZONE,
    revoked_by        VARCHAR(255)
);

CREATE INDEX IF NOT EXISTS idx_org_invitations_token_hash ON organization_invitations(token_hash);
CREATE INDEX IF NOT EXISTS idx_org_invitations_org_id ON organization_invitations(organization_id);

-- 3. Submissions dual entry tracking
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS submission_source VARCHAR(50) NOT NULL DEFAULT 'DIRECT';
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS invitation_id UUID REFERENCES organization_invitations(id) ON DELETE SET NULL;

CREATE INDEX IF NOT EXISTS idx_submissions_submission_source ON submissions(submission_source);
CREATE INDEX IF NOT EXISTS idx_submissions_invitation_id ON submissions(invitation_id);
