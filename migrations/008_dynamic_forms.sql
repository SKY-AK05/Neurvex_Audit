-- Migration 008: Dynamic Forms structure
-- This migration creates the tables needed for the dynamic Form Maker
-- and updates the submissions table to support dynamic answers.

CREATE TABLE IF NOT EXISTS form_sections (
    id SERIAL PRIMARY KEY,
    section_code VARCHAR(50) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    icon VARCHAR(50),
    summary TEXT,
    why_it_matters TEXT,
    tip TEXT,
    gating_question TEXT,
    gating_field VARCHAR(50),
    order_index INT NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS form_questions (
    id SERIAL PRIMARY KEY,
    section_id INT NOT NULL REFERENCES form_sections(id) ON DELETE CASCADE,
    field_name VARCHAR(50) UNIQUE NOT NULL,
    short_title VARCHAR(255) NOT NULL,
    question_text TEXT NOT NULL,
    order_index INT NOT NULL DEFAULT 0,
    score_mapping JSONB NOT NULL DEFAULT '{"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0, "N/A": 0}',
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Add answers column to submissions to store responses dynamically
ALTER TABLE submissions ADD COLUMN IF NOT EXISTS answers JSONB;

-- Seed initial data
-- Leadership & Culture
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('lc', 'Leadership & Culture', '◆', 
 'Assesses how neurodiversity inclusion is led and modelled by senior leadership, including accountability, culture, and psychological safety.',
 'Without visible executive commitment, neurodiversity initiatives often stall — employees notice when inclusion is only on paper.',
 'Look beyond policy documents — consider what leaders actually say and do in meetings and communications.',
 NULL, NULL, 1) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q5', 'Strategy & Direction', 'We have a clearly defined neurodiversity inclusion strategy with specific, time-bound objectives (e.g., annual goals) that are actively reviewed.', 1
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q6', 'Executive Accountability', 'A senior leader (C-suite or equivalent) is explicitly accountable for neurodiversity inclusion, with visible ownership, cross-organisation coordination, and regular monitoring of progress.', 2
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q7', 'Leadership Training & Modelling', 'Senior leaders receive training on neuro-inclusion and actively model inclusive behaviors (e.g., valuing different thinking styles, encouraging psychological safety, celebrating differences).', 3
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q8', 'Employee Resource Group', 'We have an active neurodiversity-focused employee resource group (ERG) or network that is supported, heard, and involved in shaping initiatives and decisions.', 4
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q9', 'Public Commitment', 'We publicly communicate our commitment to neuro-inclusion and demonstrate it through actions (e.g., campaigns, reporting, partnerships, inclusive employer branding).', 5
FROM form_sections WHERE section_code = 'lc' ON CONFLICT (field_name) DO NOTHING;

-- Recruitment & Onboarding
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('ro', 'Recruitment & Onboarding', '◇', 
 'Examines how inclusive hiring and onboarding practices are for neurodivergent candidates, from job design to early support and clarity.',
 'Inclusive recruitment widens your talent pool and reduces early attrition from candidates who could thrive with small adjustments.',
 'Small changes — sharing interview questions in advance or offering written tasks — can make a big difference without lowering standards.',
 NULL, NULL, 2) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q10', 'Inclusive Job Design', 'We ensure our job descriptions are clear, concise, and aligned with the actual role (tasks, expectations, outcomes), minimising jargon, with a visible commitment to inclusion.', 1
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q11', 'Transparent Application Process', 'Our application process is transparent and supportive, including clear timelines and stages, explanation of selection methods, a named contact person and multiple contact options (e.g., email, phone) to reduce uncertainty and anxiety for candidates.', 2
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q12', 'Skills-Based Assessment', 'Our selection processes include practical or skills-based assessments (e.g., work samples, task-based evaluations, project submissions) and do not rely solely on traditional interviews.', 3
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q13', 'Flexible Interviews', 'Our interviews are designed to be flexible and inclusive, with options such as providing accommodations, sharing questions in advance, allowing virtual formats or camera flexibility and being open to alternative or asynchronous responses and candidates are invited to share their preferred ways of working and need for reasonable adjustments if any.', 4
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q14', 'Structured Onboarding', 'Before starting, new hires are supported with a clear point of contact within the team, simple, structured communication about their role and expectations and early conversations about adjustments, so these can be in place from day one where possible.', 5
FROM form_sections WHERE section_code = 'ro' ON CONFLICT (field_name) DO NOTHING;

-- Work Environment & Adjustments
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('we', 'Work Environment & Adjustments', '▣', 
 'Focuses on how workplace support, flexibility, and adjustments are understood, accessed, and implemented across teams.',
 'Clear adjustment pathways and manager confidence reduce friction, build trust, and improve retention.',
 'The best adjustments are often low-cost — noise-cancelling headphones, flexible hours, or written follow-ups after meetings.',
 NULL, NULL, 3) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q15', 'Lifecycle Adjustments', 'Workplace adjustments are available and accessible at all stages of the employee lifecycle (e.g., recruitment, onboarding, day-to-day work, progression, and transitions).', 1
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q16', 'Clear Adjustment Pathways', 'There are clear, well-communicated pathways for employees to request adjustments or access support, and this information is easy to find and understand across the organisation.', 2
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q17', 'Manager & HR Training', 'Managers, HR, and people teams receive training on neurodiversity and are equipped to identify, discuss, and implement appropriate workplace adjustments confidently and consistently.', 3
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q18', 'Built-In Inclusive Practices', 'Where possible, inclusive practices are built into standard ways of working (e.g., flexible communication, clear documentation, meeting norms), reducing the need for individuals to request adjustments.', 4
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q19', 'Regular Policy Review', 'Adjustment policies and processes are regularly reviewed, using employee and manager feedback as well as data (where available) to assess effectiveness and improve over time.', 5
FROM form_sections WHERE section_code = 'we' ON CONFLICT (field_name) DO NOTHING;

-- Built Environment & Sensory
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('be', 'Built Environment & Sensory', '◎', 
 'Evaluates how physical workspaces are designed or adapted to support sensory needs and reduce environmental stress.',
 'Environmental design is often overlooked in DEI work, yet it directly impacts productivity and whether people feel safe at work.',
 'Walk through your office at peak hours — notice noise levels, lighting glare, and whether escape routes feel obvious.',
 'Does your organisation have physical workplace environments (e.g., offices, facilities, or on-site workspaces)?', 'has_physical_workspace', 4) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q20', 'Universal Design Principles', 'Workplace environments are designed or adapted using inclusive (universal design) principles to reduce sensory and accessibility barriers.', 1
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q21', 'Sensory Impact Consideration', 'We consider sensory impact in environmental decisions (e.g., lighting, noise, colours, materials, odours) and take steps to minimise common stressors.', 2
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q22', 'Varied Workspaces', 'Employees have access to different types of workspaces (e.g., quiet, low-stimulation, collaborative), rather than a one-size-fits-all environment.', 3
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q23', 'Quiet & Low-Stimulation Spaces', 'There are designated quiet or low-stimulation spaces available for employees to focus, take breaks, or regulate when needed.', 4
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q24', 'Hybrid & Remote Balance', 'Hybrid or remote work is not treated as the primary solution for inclusion; we also address barriers within the physical workplace and consider individual needs across different work settings.', 5
FROM form_sections WHERE section_code = 'be' ON CONFLICT (field_name) DO NOTHING;

-- Talent Management & Development
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('tm', 'Talent Management & Development', '↑', 
 'Assesses how performance management, feedback, learning, and career progression support neurodivergent employees.',
 'Fair talent processes ensure neurodivergent employees are developed and retained, not overlooked for roles they could excel in.',
 'Review whether performance criteria reward only one style of communication or collaboration.',
 NULL, NULL, 5) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q25', 'Inclusive Leadership Training', 'Managers and team leads are trained in inclusive leadership and are expected to apply these practices in their day-to-day management.', 1
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q26', 'Structured Feedback', 'Managers provide regular, structured feedback that is specific, evidence-based, and balanced (recognising strengths as well as areas for development).', 2
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q27', 'Wellbeing & Coaching Support', 'Employees have access to appropriate support (e.g., coaching, wellbeing resources, or specialist support where needed) to help them work effectively and build on their strengths.', 3
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q28', 'Accessible Learning & Development', 'Learning and development opportunities are designed to be accessible and inclusive by default (e.g., clear content, flexible formats, self-paced options, inclusive assessments).', 4
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q29', 'Strengths-Based Development', 'Regular career and development conversations take place, using a strengths-based approach, with clear development plans and appropriate support to help employees progress.', 5
FROM form_sections WHERE section_code = 'tm' ON CONFLICT (field_name) DO NOTHING;

-- Communication & Accessibility
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('ca', 'Communication & Accessibility', '◈', 
 'Examines how clearly and accessibly information is shared, including inclusive communication practices and formats.',
 'Accessible communication is a daily inclusion practice, not a one-off training — it benefits everyone, not only neurodivergent staff.',
 'Agendas sent 24 hours ahead and recordings of key meetings are simple wins with wide impact.',
 NULL, NULL, 6) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q30', 'Neuro-Inclusive Communication', 'Employees are trained to communicate in neuro-inclusive ways, including understanding different communication styles and how to adapt for internal and external audiences.', 1
FROM form_sections WHERE section_code = 'ca' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q31', 'Clear & Structured Communication', 'Organisational communications are typically clear, concise, and well-structured (e.g., use of plain language, bullet points, logical flow), reducing ambiguity and cognitive load.', 2
FROM form_sections WHERE section_code = 'ca' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q32', 'Accessible Formats', 'Information is available in accessible formats where needed (e.g., transcripts, captions, recordings, screen reader compatibility), and accessibility features are actively supported and encouraged.', 3
FROM form_sections WHERE section_code = 'ca' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q33', 'Inclusive Language', 'We use inclusive, respectful language when communicating about neurodiversity, and aim to frame differences in a strengths-based and non-stigmatising way.', 4
FROM form_sections WHERE section_code = 'ca' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q34', 'Feedback & Improvement', 'Employees and external stakeholders can give feedback on communication and accessibility, and there are clear mechanisms to review and improve based on that input.', 5
FROM form_sections WHERE section_code = 'ca' ON CONFLICT (field_name) DO NOTHING;

-- Products & Customer Experience
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('pc', 'Products & Customer Experience', '◉', 
 'Reviews how products, services, and customer interactions are designed to be clear, accessible, and neuro-inclusive.',
 'Neuroinclusive design improves usability for all users and reduces complaints, abandonment, and reputational risk.',
 'Involve neurodivergent users in usability testing early — you''ll catch issues that compliance checklists miss.',
 NULL, NULL, 7) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q35', 'Neuro-Inclusive Design', 'Products, services, and communication channels (e.g., websites, platforms, social media, physical materials) are designed using clear, structured, and neuro-inclusive formats.', 1
FROM form_sections WHERE section_code = 'pc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q36', 'Multiple Contact Channels', 'Customers are able to engage through a range of contact methods (e.g., email, phone, webchat, written communication), allowing them to choose what works best for them.', 2
FROM form_sections WHERE section_code = 'pc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q37', 'Sensory-Aware Environments', 'Physical customer environments are designed or adapted to reduce sensory overload where possible (e.g., managing noise, lighting, crowding, and visual stimuli).', 3
FROM form_sections WHERE section_code = 'pc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q38', 'Staff Neurodiversity Training', 'Employees involved in product design and customer service are trained in neurodiversity awareness and inclusive practices.', 4
FROM form_sections WHERE section_code = 'pc' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q39', 'Regular Inclusivity Assessment', 'We regularly assess the neuro-inclusivity of products and customer interactions (e.g., user testing, audits, feedback) and make improvements based on what we learn.', 5
FROM form_sections WHERE section_code = 'pc' ON CONFLICT (field_name) DO NOTHING;

-- Suppliers & Procurement
INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
VALUES 
('sp', 'Suppliers & Procurement', '⬡', 
 'Looks at how inclusion and accessibility are considered in supplier relationships, procurement practices, and partner engagement.',
 'Supplier standards extend your values outward and help build an ecosystem where neurodiversity-led businesses can thrive.',
 'Start by adding one inclusion question to your standard RFP template — small steps scale over time.',
 'Does your organisation have recurring engagement with external vendors, consultants, or partners?', 'has_suppliers', 8) ON CONFLICT (section_code) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q40', 'Neuro-Inclusive Supplier Comms', 'Documents and communications with suppliers are clear, structured, and presented in neuro-inclusive formats across both digital and physical channels.', 1
FROM form_sections WHERE section_code = 'sp' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q41', 'Inclusive Procurement Criteria', 'When assessing and selecting suppliers, we consider their commitment to inclusive practices, including neurodiversity where possible.', 2
FROM form_sections WHERE section_code = 'sp' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q42', 'Procurement Staff Training', 'Employees involved in procurement and supply chain management are trained in neurodiversity awareness and inclusive practices.', 3
FROM form_sections WHERE section_code = 'sp' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q43', 'Multiple Supplier Contact Methods', 'Suppliers and vendors are able to engage through a range of contact methods (e.g., email, phone, written communication), supporting different communication preferences.', 4
FROM form_sections WHERE section_code = 'sp' ON CONFLICT (field_name) DO NOTHING;

INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index)
SELECT id, 'q44', 'Supplier Feedback Mechanisms', 'There are clear opportunities for suppliers and partners to provide feedback on our processes, and this feedback is used to improve inclusivity over time.', 5
FROM form_sections WHERE section_code = 'sp' ON CONFLICT (field_name) DO NOTHING;
