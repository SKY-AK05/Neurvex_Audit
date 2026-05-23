-- Create the nd_audit database (run as superuser on your PostgreSQL Flexible Server)
-- CREATE DATABASE nd_audit;

-- Then connect to nd_audit and run:

CREATE TABLE IF NOT EXISTS submissions (
    id                SERIAL PRIMARY KEY,
    submitted_at      TIMESTAMP DEFAULT NOW(),
    name              VARCHAR(255) NOT NULL,
    company_name      VARCHAR(255) NOT NULL,
    email             VARCHAR(255) NOT NULL,
    contact_number    VARCHAR(50),
    designation       VARCHAR(255),

    -- Raw answers Q5–Q44
    q5  VARCHAR(20), q6  VARCHAR(20), q7  VARCHAR(20), q8  VARCHAR(20), q9  VARCHAR(20),
    q10 VARCHAR(20), q11 VARCHAR(20), q12 VARCHAR(20), q13 VARCHAR(20), q14 VARCHAR(20),
    q15 VARCHAR(20), q16 VARCHAR(20), q17 VARCHAR(20), q18 VARCHAR(20), q19 VARCHAR(20),
    q20 VARCHAR(20), q21 VARCHAR(20), q22 VARCHAR(20), q23 VARCHAR(20), q24 VARCHAR(20),
    q25 VARCHAR(20), q26 VARCHAR(20), q27 VARCHAR(20), q28 VARCHAR(20), q29 VARCHAR(20),
    q30 VARCHAR(20), q31 VARCHAR(20), q32 VARCHAR(20), q33 VARCHAR(20), q34 VARCHAR(20),
    q35 VARCHAR(20), q36 VARCHAR(20), q37 VARCHAR(20), q38 VARCHAR(20), q39 VARCHAR(20),
    q40 VARCHAR(20), q41 VARCHAR(20), q42 VARCHAR(20), q43 VARCHAR(20), q44 VARCHAR(20),

    -- Section scores and levels
    lc_score INT,         lc_level VARCHAR(50),
    ro_score INT,         ro_level VARCHAR(50),
    we_score INT,         we_level VARCHAR(50),
    be_score INT,         be_level VARCHAR(50),
    tm_score INT,         tm_level VARCHAR(50),
    ca_score INT,         ca_level VARCHAR(50),
    pc_score INT,         pc_level VARCHAR(50),
    sp_score INT,         sp_level VARCHAR(50),

    -- Overall
    overall_avg   DECIMAL(4,2),
    overall_level VARCHAR(50),

    -- Email and status
    email_body    TEXT,
    status        VARCHAR(20) DEFAULT 'pending',
    sent_at       TIMESTAMP
);

CREATE TABLE IF NOT EXISTS app_settings (
    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
    notification_email      VARCHAR(255) NOT NULL DEFAULT '',
    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
    updated_at              TIMESTAMP DEFAULT NOW()
);

INSERT INTO app_settings (
    id, sender_name, sender_address,
    notification_email, notifications_enabled, support_email
)
VALUES (
    1, 'Orchvate', '',
    'aakash.padyachi@rochvate.com', FALSE, 'aakash.padyachi@rochvate.com'
)
ON CONFLICT (id) DO NOTHING;

-- See sql/README.md for migration scripts (notifications + support)
