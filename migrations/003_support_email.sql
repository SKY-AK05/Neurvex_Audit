-- DEPRECATED: use sql/02_support_requests.sql or sql/install_all.sql

-- Support request recipient email. Run on nd_audit database.

ALTER TABLE app_settings
ADD COLUMN IF NOT EXISTS support_email VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com';

UPDATE app_settings
SET support_email = 'aakash.padyachi@rochvate.com'
WHERE id = 1 AND (support_email IS NULL OR support_email = '');
