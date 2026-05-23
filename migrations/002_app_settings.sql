-- DEPRECATED: use sql/01_admin_notifications.sql and sql/02_support_requests.sql
-- Or run sql/install_all.sql for a full setup.

-- App settings (sender + admin notifications). Run on nd_audit database.

CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);

INSERT INTO app_settings (id, sender_name, sender_address)
VALUES (1, 'Orchvate', '')
ON CONFLICT (id) DO NOTHING;
