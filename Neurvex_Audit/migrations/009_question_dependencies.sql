-- Migration: 009_question_dependencies.sql
-- Description: Add depends_on_field and depends_on_value to form_questions for question-level dependencies

ALTER TABLE form_questions
ADD COLUMN IF NOT EXISTS depends_on_field VARCHAR(255),
ADD COLUMN IF NOT EXISTS depends_on_value VARCHAR(255);
