-- 007_fix_score_columns.sql
-- The scoring service returns DECIMAL values (e.g. 12.5 from NA-rescaling).
-- The original create_table.sql defined these as INT, causing insert failures.
-- Also adds the gating-question answer columns used by routing.py.

-- Fix score columns: INT -> DECIMAL(5,2)
ALTER TABLE submissions
    ALTER COLUMN lc_score TYPE DECIMAL(5,2) USING lc_score::DECIMAL,
    ALTER COLUMN ro_score TYPE DECIMAL(5,2) USING ro_score::DECIMAL,
    ALTER COLUMN we_score TYPE DECIMAL(5,2) USING we_score::DECIMAL,
    ALTER COLUMN be_score TYPE DECIMAL(5,2) USING be_score::DECIMAL,
    ALTER COLUMN tm_score TYPE DECIMAL(5,2) USING tm_score::DECIMAL,
    ALTER COLUMN ca_score TYPE DECIMAL(5,2) USING ca_score::DECIMAL,
    ALTER COLUMN pc_score TYPE DECIMAL(5,2) USING pc_score::DECIMAL,
    ALTER COLUMN sp_score TYPE DECIMAL(5,2) USING sp_score::DECIMAL;

-- Add gating-question columns for "Built Environment" and "Suppliers" sections
-- (used in routes.py INSERT; scoring_service reads them from submitted data dict)
ALTER TABLE submissions
    ADD COLUMN IF NOT EXISTS has_physical_workspace VARCHAR(10),
    ADD COLUMN IF NOT EXISTS has_suppliers          VARCHAR(10);

-- Widen the level columns just in case (was 50, keep 50 as it fits "Not applicable")
-- No change needed for level columns.

-- Notification: run this once against the live DB before the next deployment.
