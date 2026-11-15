-- =============================================================================
-- Migration 018: Secure Organisation Assessment Access Tokens
-- Enables opaque random tokens (/audit?t=SECURE_TOKEN) to protect organisation
-- identity in URLs, support campaigns, and enforce secure assessment contexts.
-- =============================================================================

CREATE TABLE IF NOT EXISTS assessment_access_tokens (
    id                UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    token_hash        VARCHAR(64) NOT NULL UNIQUE,
    token             VARCHAR(255) NULL,
    organisation_id   UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    campaign_id       UUID NULL,
    name              VARCHAR(255) NULL,
    is_default        BOOLEAN NOT NULL DEFAULT FALSE,
    created_by        VARCHAR(255) NULL,
    created_at        TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    expires_at        TIMESTAMP WITH TIME ZONE NULL,
    revoked_at        TIMESTAMP WITH TIME ZONE NULL,
    revoked_by        VARCHAR(255) NULL
);

-- Indexes for high-speed resolution and tenant lookups
CREATE UNIQUE INDEX IF NOT EXISTS idx_access_tokens_token_hash ON assessment_access_tokens(token_hash);
CREATE INDEX IF NOT EXISTS idx_access_tokens_org_id ON assessment_access_tokens(organisation_id);
CREATE INDEX IF NOT EXISTS idx_access_tokens_active ON assessment_access_tokens(organisation_id) WHERE revoked_at IS NULL;
CREATE INDEX IF NOT EXISTS idx_access_tokens_default ON assessment_access_tokens(organisation_id) WHERE is_default = TRUE AND revoked_at IS NULL;

-- Submissions binding to secure assessment tokens and campaigns
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS access_token_id UUID REFERENCES assessment_access_tokens(id) ON DELETE SET NULL;
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS campaign_id UUID NULL;

CREATE INDEX IF NOT EXISTS idx_submissions_access_token_id ON submissions(access_token_id);
CREATE INDEX IF NOT EXISTS idx_submissions_campaign_id ON submissions(campaign_id);

