-- =============================================================================
-- Migration 019: Admin-Configurable System Security & Rate Limit Settings
-- Provides dynamic runtime configuration for submission rate limits,
-- session attempt bounds, and abuse protection without redeployment.
-- =============================================================================

CREATE TABLE IF NOT EXISTS system_security_settings (
    id            SERIAL PRIMARY KEY,
    setting_key   VARCHAR(100) NOT NULL UNIQUE,
    setting_value TEXT NOT NULL,
    description   TEXT NULL,
    updated_at    TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_by    VARCHAR(255) NOT NULL DEFAULT 'system'
);

CREATE INDEX IF NOT EXISTS idx_system_security_settings_key ON system_security_settings(setting_key);

-- Seed initial defaults
INSERT INTO system_security_settings (setting_key, setting_value, description, updated_by)
VALUES
    ('submit_rate_limit_hour', '500', 'Public submissions per IP per hour', 'system-init'),
    ('submit_rate_limit_day', '2000', 'Public submissions per IP per day', 'system-init'),
    ('secure_submit_rate_limit_hour', '500', 'Secure-link submissions per IP per hour', 'system-init'),
    ('secure_submit_rate_limit_day', '2000', 'Secure-link submissions per IP per day', 'system-init'),
    ('assessment_session_limit_hour', '3', 'Assessment session attempts per hour', 'system-init'),
    ('invalid_token_limit_minute', '10', 'Invalid-token attempts per IP per minute', 'system-init')
ON CONFLICT (setting_key) DO NOTHING;
