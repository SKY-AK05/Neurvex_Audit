-- =============================================================================
-- Support requests (Support page in NeuroMark)
-- =============================================================================
-- When a user submits the support form, the message is emailed to support_email.
--
-- Requires: sql/01_admin_notifications.sql (creates app_settings table)
--
-- Run on database: nd_audit
--   psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/02_support_requests.sql
-- =============================================================================

-- Create settings table if 01 was not run yet (includes support column)
CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- Add support inbox column on existing databases
ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS support_email VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com';

-- Ensure settings row exists
INSERT INTO app_settings (id, sender_name, sender_address, support_email)
VALUES (1, 'Orchvate', '', 'aakash.padyachi@rochvate.com')
ON CONFLICT (id) DO NOTHING;

-- Set default support inbox if still empty
UPDATE app_settings
SET support_email = 'aakash.padyachi@rochvate.com'
WHERE id = 1
  AND (support_email IS NULL OR TRIM(support_email) = '');

COMMENT ON COLUMN app_settings.support_email IS
    'Inbox for Support page form submissions (NeuroMark → Support)';
