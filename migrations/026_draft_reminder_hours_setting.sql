-- Migration 026: Add draft_reminder_hours to app_settings
-- Enables SuperAdmin to configure the inactivity delay before incomplete assessment reminders are sent.

ALTER TABLE app_settings
ADD COLUMN IF NOT EXISTS draft_reminder_hours INT NOT NULL DEFAULT 2;

UPDATE app_settings
SET draft_reminder_hours = 2
WHERE draft_reminder_hours IS NULL;
