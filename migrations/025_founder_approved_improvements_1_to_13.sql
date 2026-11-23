-- Migration 025: Synchronize Founder-Approved NIWI Improvements (Items 6–13)
-- Updates gating questions and question texts in database to match defaultSections.js.
-- Note: Item 14 (Psychological Safety) is explicitly on hold and excluded.

-- Item 6 (NIWI-026): Section 4 (Built Environment) gating question
UPDATE form_sections
SET gating_question = 'Does your organisation provide or manage physical workplace environments where employees regularly work (e.g., offices, facilities, or on-site workspaces)?',
    updated_at = NOW()
WHERE section_code = 'be';

-- Item 7 (NIWI-028): Section 4, Q20 (Field q24) Hybrid & Remote Balance
UPDATE form_questions
SET question_text = 'Our organisation addresses sensory barriers within physical workplaces rather than relying on remote or hybrid work as the primary solution for inclusion.',
    updated_at = NOW()
WHERE field_name = 'q24';

-- Item 8 (NIWI-029): Section 5, Q21 (Field q25) Inclusive Leadership Training
UPDATE form_questions
SET question_text = 'Managers and team leads are trained on inclusive leadership practices and apply them in their day-to-day management.',
    updated_at = NOW()
WHERE field_name = 'q25';

-- Item 12 (Roshan Rec 1): Section 3, Q13 (Field q17) Manager & HR Training
UPDATE form_questions
SET question_text = 'Managers, HR, and people teams receive training on neurodiversity and are equipped to identify, discuss, and implement workplace adjustments tailored to individual needs.',
    updated_at = NOW()
WHERE field_name = 'q17';

-- Item 13 (Roshan Rec 2): Section 6, Q27 (Field q31) Clear & Structured Communication
UPDATE form_questions
SET question_text = 'Instructions, expectations, feedback and deadlines are communicated clearly, consistently and in a structured way to reduce ambiguity and support different information-processing needs.',
    updated_at = NOW()
WHERE field_name = 'q31';

-- Item 9 (NIWI-032): Section 6, Q30 (Field q34) Feedback & Improvement
UPDATE form_questions
SET question_text = 'Our organisation has structured mechanisms to collect, review and act on feedback from employees and external stakeholders on communication and accessibility.',
    updated_at = NOW()
WHERE field_name = 'q34';

-- Item 10 (NIWI-033): Section 7, Q31 (Field q35) Neuro-Inclusive Design
UPDATE form_questions
SET question_text = 'The organisation applies clear, structured and neuro-inclusive design principles across all its products, services and customer communication channels, including websites, digital platforms, social media and physical materials.',
    updated_at = NOW()
WHERE field_name = 'q35';

-- Item 11 (NIWI-036): Section 8 (Suppliers & Procurement) gating question
UPDATE form_sections
SET gating_question = 'Does your organisation engage with external suppliers?',
    updated_at = NOW()
WHERE section_code = 'sp';
