-- Migration 013: Organization-Admin Mapping & Authorization
-- Creates the missing organization_admins table to establish which admins
-- have access to which organizations, enabling org-level access control.

-- Create organization_admins mapping table
CREATE TABLE IF NOT EXISTS organization_admins (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_email VARCHAR(255) NOT NULL,
    organization_id UUID NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    created_by VARCHAR(255),
    
    -- Constraints
    CONSTRAINT fk_organization_admins_org 
        FOREIGN KEY (organization_id) 
        REFERENCES organizations(id) 
        ON DELETE CASCADE,
    CONSTRAINT uq_organization_admins_email_org 
        UNIQUE (admin_email, organization_id)
);

-- Index for faster lookups
CREATE INDEX IF NOT EXISTS idx_organization_admins_email 
    ON organization_admins(admin_email);
CREATE INDEX IF NOT EXISTS idx_organization_admins_org 
    ON organization_admins(organization_id);

-- Note: Super admins have access to ALL organizations without explicit mapping
-- Admin users only see organizations they're explicitly assigned to
-- This follows principle of least privilege for production security
