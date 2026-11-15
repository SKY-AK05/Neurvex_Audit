ALTER TABLE admin_users ALTER COLUMN password_hash DROP NOT NULL;
ALTER TABLE admin_users ALTER COLUMN name DROP NOT NULL;

-- Ensure email is unique
DO $$ 
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM pg_constraint WHERE conname = 'admin_users_email_key'
  ) THEN
    ALTER TABLE admin_users ADD CONSTRAINT admin_users_email_key UNIQUE (email);
  END IF;
END $$;

INSERT INTO admin_users (email, role) VALUES
    ('aakash.padyachi@orchvate.com', 'super'),
    ('mamta.kamath@orchvate.com', 'admin'),
    ('panchali.banerjee@orchvate.com', 'admin'),
    ('rahul.rajesh@orchvate.com', 'admin'),
    ('geethanjali.ganapathy@orchvate.com', 'admin')
ON CONFLICT (email) DO NOTHING;
