-- Migration 027: Add draft_reminder_value and draft_reminder_unit to app_settings
-- Allows SuperAdmin to configure inactivity threshold in seconds, minutes, or hours.

ALTER TABLE app_settings
ADD COLUMN IF NOT EXISTS draft_reminder_value INT NOT NULL DEFAULT 2;

ALTER TABLE app_settings
ADD COLUMN IF NOT EXISTS draft_reminder_unit VARCHAR(10) NOT NULL DEFAULT 'hours';

UPDATE app_settings
SET draft_reminder_value = COALESCE(draft_reminder_hours, 2),
    draft_reminder_unit = 'hours'
WHERE draft_reminder_unit IS NULL OR draft_reminder_value IS NULL;
