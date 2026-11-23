-- Migration 024: Draft reminders and 30-day lifecycle support
ALTER TABLE draft_submissions 
ADD COLUMN IF NOT EXISTS reminder_sent_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS reminder_count INT NOT NULL DEFAULT 0;

CREATE INDEX IF NOT EXISTS idx_draft_submissions_reminder 
ON draft_submissions(submitted, updated_at, reminder_sent_at)
WHERE submitted = FALSE;
