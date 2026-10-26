"""
test_filter_builder.py — Tests for ServiceNow-style query building, validation, and execution.
"""
import pytest
from app.services.filter_service import (
    build_filter_query,
    build_condition_sql,
    ALLOWED_FILTER_FIELDS,
    ALLOWED_OPERATORS,
)


def test_allowed_fields_and_operators_structure():
    assert "company_name" in ALLOWED_FILTER_FIELDS
    assert "status" in ALLOWED_FILTER_FIELDS
    assert "overall_avg" in ALLOWED_FILTER_FIELDS
    assert "submitted_at" in ALLOWED_FILTER_FIELDS

    assert "contains" in ALLOWED_OPERATORS["text"]
    assert "is_one_of" in ALLOWED_OPERATORS["enum"]
    assert "greater_than_or_equal" in ALLOWED_OPERATORS["numeric"]
    assert "between" in ALLOWED_OPERATORS["date"]


def test_single_text_condition():
    cond = {"field": "company_name", "operator": "contains", "value": "Acme"}
    sql, params, summary = build_condition_sql(cond)
    assert sql == "company_name ILIKE %s"
    assert params == ["%Acme%"]
    assert summary == 'Organization Name contains "Acme"'


def test_enum_is_one_of_condition():
    cond = {"field": "status", "operator": "is_one_of", "values": ["sent", "pending"]}
    sql, params, summary = build_condition_sql(cond)
    assert sql == "status IN (%s, %s)"
    assert params == ["sent", "pending"]
    assert summary == "Status is one of (sent, pending)"


def test_numeric_between_condition():
    cond = {"field": "overall_avg", "operator": "between", "value": 10, "value_to": 18}
    sql, params, summary = build_condition_sql(cond)
    assert sql == "overall_avg BETWEEN %s AND %s"
    assert params == [10.0, 18.0]
    assert summary == "Overall Score between 10.0 and 18.0"


def test_date_is_after_condition():
    cond = {"field": "submitted_at", "operator": "is_after", "value": "2026-01-15"}
    sql, params, summary = build_condition_sql(cond)
    assert sql == "DATE(submitted_at) > %s"
    assert params == ["2026-01-15"]
    assert summary == "Sent Date & Time is after 2026-01-15"


def test_empty_and_not_empty_operators():
    sql1, params1, sum1 = build_condition_sql({"field": "designation", "operator": "is_empty"})
    assert "IS NULL" in sql1
    assert len(params1) == 0

    sql2, params2, sum2 = build_condition_sql({"field": "email", "operator": "is_not_empty"})
    assert "IS NOT NULL" in sql2
    assert len(params2) == 0


def test_reject_unsupported_field():
    with pytest.raises(ValueError, match="Unsupported or invalid filter field"):
        build_condition_sql({"field": "passwords_hash; DROP TABLE submissions;", "operator": "is", "value": "x"})


def test_reject_unsupported_operator_for_type():
    # Numeric field with text operator 'contains'
    with pytest.raises(ValueError, match="not valid for field"):
        build_condition_sql({"field": "overall_avg", "operator": "contains", "value": "10"})


def test_reject_malformed_date():
    with pytest.raises(ValueError, match="Invalid date format"):
        build_condition_sql({"field": "submitted_at", "operator": "is", "value": "not-a-date"})


def test_and_or_group_query_construction():
    filter_groups = [
        {
            "logical_operator": "AND",
            "conditions": [
                {"field": "status", "operator": "is", "value": "sent"},
                {"field": "overall_avg", "operator": "greater_than_or_equal", "value": 15},
            ],
        },
        {
            "logical_operator": "OR",
            "conditions": [
                {"field": "company_name", "operator": "contains", "value": "Orchvate"},
                {"field": "company_name", "operator": "contains", "value": "NeuroMark"},
            ],
        },
    ]

    sort_by = [{"field": "submitted_at", "direction": "desc"}]
    data_sql, count_sql, params, summary = build_filter_query(
        filter_groups=filter_groups,
        sort_by=sort_by,
        page=1,
        per_page=10,
    )

    # Check parameterized query
    assert "WHERE" in data_sql
    assert "SELECT COUNT(*) FROM submissions" in count_sql
    assert "status = %s" in data_sql
    assert "overall_avg >= %s" in data_sql
    assert "company_name ILIKE %s" in data_sql
    assert "ORDER BY submitted_at DESC" in data_sql
    assert "LIMIT 10 OFFSET 0" in data_sql

    assert "All >" in summary
    assert "Status is \"sent\"" in summary
    assert ".or." in summary or ".and." in summary
    assert len(params) == 4


def test_sorting_and_pagination_bounds():
    data_sql, count_sql, params, _ = build_filter_query(
        filter_groups=[],
        sort_by=[{"field": "company_name", "direction": "asc"}],
        page=3,
        per_page=25,
    )
    assert "LIMIT 25 OFFSET 50" in data_sql
    assert "company_name ASC" in data_sql


def test_organization_isolation_enforcement():
    data_sql, count_sql, params, summary = build_filter_query(
        filter_groups=[],
        organization_id="11111111-2222-3333-4444-555555555555",
    )
    assert "organization_id = %s" in data_sql
    assert "organization_id = %s" in count_sql
    assert "11111111-2222-3333-4444-555555555555" in params
    assert "Organization ID =" in summary
