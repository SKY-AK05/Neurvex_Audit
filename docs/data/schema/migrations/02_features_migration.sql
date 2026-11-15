-- Feature 1: Progress Saving
CREATE TABLE IF NOT EXISTS draft_submissions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    company_name VARCHAR(255) NOT NULL,
    form_state JSONB NOT NULL,
    current_step INT NOT NULL DEFAULT 0,
    submitted BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_draft_submissions_email ON draft_submissions(email);

-- Feature 2: Persistent Org Accounts
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS organization_users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    email VARCHAR(255) UNIQUE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_org_users_email ON organization_users(email);

-- Link submissions to organizations
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS organization_id UUID REFERENCES organizations(id) ON DELETE SET NULL;
CREATE INDEX IF NOT EXISTS idx_submissions_org_id ON submissions(organization_id);

-- Feature 3: CRM Integration
ALTER TABLE app_settings 
ADD COLUMN IF NOT EXISTS crm_sync_enabled BOOLEAN NOT NULL DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS hubspot_api_key VARCHAR(255) DEFAULT '';

-- Feature 4: Dimension-Level Breakdown
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS dimension_scores JSONB;
