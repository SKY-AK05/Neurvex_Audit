-- Migration 023: Update Q9 (q13) Flexible Interviews question text
-- Simplifies the sentence and groups interview accommodations into a short list.

UPDATE form_questions
SET question_text = 'Our interview process is flexible and inclusive, with reasonable adjustments offered based on individual needs (e.g., questions shared in advance, virtual interviews, camera flexibility or alternative response formats). Candidates are invited to share their preferred ways of working and any adjustments they may need.'
WHERE field_name = 'q13';
