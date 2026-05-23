-- =============================================================================
-- Admin user notifications (bell icon in Neurvex)
-- =============================================================================
-- When notifications_enabled = TRUE, the admin at notification_email receives
-- an email each time someone submits a new Neurvex Audit.
--
-- Run on database: nd_audit
--   psql -h YOUR_HOST -U YOUR_USER -d nd_audit -f sql/01_admin_notifications.sql
-- =============================================================================

-- Settings table (single row, id = 1)
CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    updated_at              TIMESTAMP DEFAULT NOW()
);

-- Upgrade: add notification columns if table existed from an older schema
ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS notification_email VARCHAR(255) NOT NULL DEFAULT '';

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS notifications_enabled BOOLEAN NOT NULL DEFAULT FALSE;

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS sender_name VARCHAR(255) NOT NULL DEFAULT 'Orchvate';

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS sender_address VARCHAR(255) NOT NULL DEFAULT '';

ALTER TABLE app_settings
    ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP DEFAULT NOW();

-- Ensure the single settings row exists
INSERT INTO app_settings (
    id,
    sender_name,
    sender_address,
    notification_email,
    notifications_enabled
)
VALUES (
    1,
    'Orchvate',
    '',
    'aakash.padyachi@rochvate.com',
    FALSE
)
ON CONFLICT (id) DO NOTHING;

-- Set default notification inbox if still empty (edit email below if needed)
UPDATE app_settings
SET notification_email = 'aakash.padyachi@rochvate.com'
WHERE id = 1
  AND (notification_email IS NULL OR TRIM(notification_email) = '');

COMMENT ON COLUMN app_settings.notification_email IS
    'Admin inbox: receives email when a new audit is submitted (if notifications_enabled)';

COMMENT ON COLUMN app_settings.notifications_enabled IS
    'TRUE when admin turned on bell alerts in the Neurvex header';
