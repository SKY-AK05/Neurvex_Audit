-- =============================================================================
-- Migration 006: Multi-respondent org scoring
-- Run on database: nd_audit
-- =============================================================================

-- Weighted join table between orgs and submissions
CREATE TABLE IF NOT EXISTS org_submission_links (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    submission_id UUID NOT NULL REFERENCES submissions(id)  ON DELETE CASCADE,
    weight        FLOAT NOT NULL DEFAULT 1.0,
    linked_by     VARCHAR(255),          -- NULL = auto-linked at submit time; admin email = manual
    linked_at     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE (org_id, submission_id)
);

CREATE INDEX IF NOT EXISTS idx_osl_org_id        ON org_submission_links(org_id);
CREATE INDEX IF NOT EXISTS idx_osl_submission_id ON org_submission_links(submission_id);

-- Ad-hoc admin messages sent to org respondents
CREATE TABLE IF NOT EXISTS admin_messages (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id        UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    submission_id UUID REFERENCES submissions(id) ON DELETE SET NULL,  -- NULL = broadcast to all
    sent_by       VARCHAR(255) NOT NULL,
    subject       VARCHAR(500) NOT NULL,
    body          TEXT NOT NULL,
    recipients    JSONB NOT NULL DEFAULT '[]',   -- [{email, name}, ...]
    sent_at       TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_admin_messages_org_id ON admin_messages(org_id);

-- Back-fill: create org_submission_links rows for submissions that already have
-- an organization_id set (from the existing auto-link-by-email logic in org.py).
-- Weight defaults to 1.0, linked_by NULL (treated as auto-linked).
INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
SELECT organization_id, id, 1.0, NULL
FROM   submissions
WHERE  organization_id IS NOT NULL
ON CONFLICT (org_id, submission_id) DO NOTHING;
