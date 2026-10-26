-- =============================================================================
-- Migration 010: Saved Filters for Admin Submissions Dashboard
-- Supports ServiceNow-style reusable filter configurations
-- =============================================================================

CREATE TABLE IF NOT EXISTS saved_filters (
    id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name          VARCHAR(255) NOT NULL,
    description   TEXT,
    filter_config JSONB NOT NULL,
    created_by    VARCHAR(255) NOT NULL DEFAULT 'system',
    is_shared     BOOLEAN NOT NULL DEFAULT TRUE,
    created_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at    TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_saved_filters_created_by ON saved_filters(created_by);

-- Insert standard system preset filters
INSERT INTO saved_filters (id, name, description, filter_config, created_by, is_shared)
VALUES 
    (
        '11111111-1111-1111-1111-111111111111',
        'All Submissions',
        'Default view showing all submissions ordered by date',
        '{"filter_groups": [], "sort_by": [{"field": "submitted_at", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '22222222-2222-2222-2222-222222222222',
        'Pending Review',
        'Submissions pending email review and delivery',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "status", "operator": "is", "value": "pending"}]}], "sort_by": [{"field": "submitted_at", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '33333333-3333-3333-3333-333333333333',
        'Delivered Reports',
        'Submissions with delivered audit reports',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "status", "operator": "is", "value": "sent"}]}], "sort_by": [{"field": "submitted_at", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '44444444-4444-4444-4444-444444444444',
        'High Maturity (Developing)',
        'Organisations achieving developing maturity stage (score >= 15)',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "overall_avg", "operator": "greater_than_or_equal", "value": "15"}]}], "sort_by": [{"field": "overall_avg", "direction": "desc"}]}',
        'system',
        TRUE
    ),
    (
        '55555555-5555-5555-5555-555555555555',
        'Foundational Priority',
        'Organisations in foundational stage needing support (score <= 6)',
        '{"filter_groups": [{"logical_operator": "AND", "conditions": [{"field": "overall_avg", "operator": "less_than_or_equal", "value": "6"}]}], "sort_by": [{"field": "overall_avg", "direction": "asc"}]}',
        'system',
        TRUE
    )
ON CONFLICT (id) DO NOTHING;
