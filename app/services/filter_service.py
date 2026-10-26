"""
filter_service.py — Safe server-side query builder for ServiceNow-style filter execution.

Validates filter expressions against a strict allowlist of columns and data types.
Generates parameterized SQL queries to prevent SQL injection and ensure predictable AND/OR semantics.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import re

# Strict allowlist of filterable fields, their DB column mapping, and their data type
ALLOWED_FILTER_FIELDS = {
    "company_name": {
        "column": "company_name",
        "type": "text",
        "label": "Organization Name",
    },
    "name": {
        "column": "name",
        "type": "text",
        "label": "Respondent Name",
    },
    "email": {
        "column": "email",
        "type": "text",
        "label": "Recipient Email",
    },
    "designation": {
        "column": "designation",
        "type": "text",
        "label": "Job Role / Designation",
    },
    "contact_number": {
        "column": "contact_number",
        "type": "text",
        "label": "Contact Number",
    },
    "status": {
        "column": "status",
        "type": "enum",
        "label": "Status",
        "options": ["pending", "sending", "sent", "failed"],
    },
    "overall_level": {
        "column": "overall_level",
        "type": "enum",
        "label": "Maturity Level",
        "options": [
            "Level 1 — Foundational",
            "Level 2 — Early Progress",
            "Level 3 — Developing",
        ],
    },
    "overall_avg": {
        "column": "overall_avg",
        "type": "numeric",
        "label": "Overall Score",
    },
    "lc_score": {
        "column": "lc_score",
        "type": "numeric",
        "label": "Leadership & Culture Score",
    },
    "ro_score": {
        "column": "ro_score",
        "type": "numeric",
        "label": "Recruitment & Onboarding Score",
    },
    "we_score": {
        "column": "we_score",
        "type": "numeric",
        "label": "Work Environment Score",
    },
    "be_score": {
        "column": "be_score",
        "type": "numeric",
        "label": "Built Environment Score",
    },
    "tm_score": {
        "column": "tm_score",
        "type": "numeric",
        "label": "Talent Management Score",
    },
    "ca_score": {
        "column": "ca_score",
        "type": "numeric",
        "label": "Communication & Accessibility Score",
    },
    "pc_score": {
        "column": "pc_score",
        "type": "numeric",
        "label": "Products & Customer Service Score",
    },
    "sp_score": {
        "column": "sp_score",
        "type": "numeric",
        "label": "Supply Chain & Procurement Score",
    },
    "submitted_at": {
        "column": "submitted_at",
        "type": "date",
        "label": "Sent Date & Time",
    },
    "id": {
        "column": "id",
        "type": "text",
        "label": "Submission ID",
    },
    # ── Demographics stored in answers JSONB ────────────────────────────────
    # The column value uses PostgreSQL JSONB text extraction: answers->>'key'
    # All text/enum operators work correctly against these expressions.
    "function": {
        "column": "answers->>'function'",
        "type": "enum",
        "label": "Function / Department",
        "options": [
            "Administration", "Engineering", "ESG / Sustainability", "Finance",
            "HR / People", "Legal & Compliance", "Manufacturing / Production",
            "Marketing & Communications", "Operations", "Project Management",
            "Quality Assurance / Quality Control", "Research & Development (R&D)",
            "Sales & Business Development", "Supply Chain / Procurement / Logistics",
            "Technology / IT / Product Management", "Other",
        ],
    },
    "role": {
        "column": "answers->>'role'",
        "type": "enum",
        "label": "Role Level",
        "options": [
            "Individual Contributor / Team Member",
            "People Manager/Supervisor",
            "Head of Function/Director",
            "VP / Senior Leader",
            "C-Suite / Executive",
            "Board Member / Trustee",
            "Consultant / Advisor",
            "Other",
        ],
    },
    "country": {
        "column": "answers->>'country'",
        "type": "text",
        "label": "Country",
    },
    "state_ut": {
        "column": "answers->>'state_ut'",
        "type": "text",
        "label": "State / UT (India)",
    },
    "gender": {
        "column": "answers->>'gender'",
        "type": "enum",
        "label": "Gender Identity",
        "options": [
            "Man", "Woman", "Non-binary / Gender non-conforming",
            "Prefer not to say", "Other gender identity",
        ],
    },
    "is_pwd": {
        "column": "answers->>'is_pwd'",
        "type": "enum",
        "label": "Person with Disability (PwD)",
        "options": ["Yes", "No", "Prefer not to say"],
    },
    "is_neurodivergent": {
        "column": "answers->>'is_neurodivergent'",
        "type": "enum",
        "label": "Neurodivergent",
        "options": ["Yes", "No", "Prefer not to say"],
    },
    "is_marginalized": {
        "column": "answers->>'is_marginalized'",
        "type": "enum",
        "label": "Underrepresented / Marginalized",
        "options": ["Yes", "No", "Prefer not to say"],
    },
}

ALLOWED_SORT_FIELDS = set(ALLOWED_FILTER_FIELDS.keys())

ALLOWED_OPERATORS = {
    "text": {
        "is",
        "is_not",
        "contains",
        "does_not_contain",
        "starts_with",
        "ends_with",
        "is_empty",
        "is_not_empty",
    },
    "enum": {
        "is",
        "is_not",
        "is_one_of",
        "is_not_one_of",
        "is_empty",
        "is_not_empty",
    },
    "numeric": {
        "equals",
        "does_not_equal",
        "greater_than",
        "less_than",
        "greater_than_or_equal",
        "less_than_or_equal",
        "between",
        "is_empty",
        "is_not_empty",
    },
    "date": {
        "is",
        "is_before",
        "is_after",
        "is_on_or_before",
        "is_on_or_after",
        "between",
        "is_empty",
        "is_not_empty",
    },
}


def _validate_date_str(val: str) -> str:
    """Validate and sanitize YYYY-MM-DD date string."""
    if not isinstance(val, str):
        raise ValueError("Date value must be a string in YYYY-MM-DD format")
    val = val.strip()
    # Accept ISO strings or standard date formats
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", val)
    if not m:
        raise ValueError(f"Invalid date format: '{val}'. Expected YYYY-MM-DD")
    try:
        datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid calendar date '{val}': {e}")
    return m.group(1)


def _validate_numeric(val: Any) -> float:
    """Validate numeric input."""
    try:
        return float(val)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric value: '{val}'")


def build_condition_sql(condition: Dict[str, Any]) -> Tuple[str, List[Any], str]:
    """
    Build SQL clause, parameter list, and readable summary for a single condition.
    Returns: (sql_fragment, params, human_readable_summary)
    """
    field_key = condition.get("field")
    if not field_key or field_key not in ALLOWED_FILTER_FIELDS:
        raise ValueError(f"Unsupported or invalid filter field: '{field_key}'")

    meta = ALLOWED_FILTER_FIELDS[field_key]
    col = meta["column"]
    data_type = meta["type"]
    label = meta["label"]

    raw_op = condition.get("operator", "is")
    # Normalize operator string (replace spaces or hyphens with underscores)
    op = raw_op.lower().replace(" ", "_").replace("-", "_")

    # Map aliases
    if op == "equal" or op == "equals":
        op = "equals" if data_type == "numeric" else "is"
    elif op == "not_equal" or op == "does_not_equal":
        op = "does_not_equal" if data_type == "numeric" else "is_not"

    if op not in ALLOWED_OPERATORS.get(data_type, set()):
        raise ValueError(f"Operator '{raw_op}' is not valid for field '{field_key}' ({data_type})")

    val = condition.get("value")
    val_to = condition.get("value_to")
    vals = condition.get("values") or []

    # 1. Empty / Not Empty
    if op == "is_empty":
        if data_type in ("text", "enum"):
            return f"({col} IS NULL OR TRIM(CAST({col} AS TEXT)) = '')", [], f"{label} is empty"
        else:
            return f"({col} IS NULL)", [], f"{label} is empty"

    if op == "is_not_empty":
        if data_type in ("text", "enum"):
            return f"({col} IS NOT NULL AND TRIM(CAST({col} AS TEXT)) != '')", [], f"{label} is not empty"
        else:
            return f"({col} IS NOT NULL)", [], f"{label} is not empty"

    # 2. Text fields
    if data_type == "text":
        str_val = str(val or "").strip()
        if op == "is":
            return f"{col} = %s", [str_val], f"{label} is \"{str_val}\""
        elif op == "is_not":
            return f"({col} != %s OR {col} IS NULL)", [str_val], f"{label} is not \"{str_val}\""
        elif op == "contains":
            return f"{col} ILIKE %s", [f"%{str_val}%"], f"{label} contains \"{str_val}\""
        elif op == "does_not_contain":
            return f"({col} NOT ILIKE %s OR {col} IS NULL)", [f"%{str_val}%"], f"{label} does not contain \"{str_val}\""
        elif op == "starts_with":
            return f"{col} ILIKE %s", [f"{str_val}%"], f"{label} starts with \"{str_val}\""
        elif op == "ends_with":
            return f"{col} ILIKE %s", [f"%{str_val}"], f"{label} ends with \"{str_val}\""

    # 3. Enumerated fields
    if data_type == "enum":
        if op == "is":
            str_val = str(val or "").strip()
            return f"{col} = %s", [str_val], f"{label} is \"{str_val}\""
        elif op == "is_not":
            str_val = str(val or "").strip()
            return f"({col} != %s OR {col} IS NULL)", [str_val], f"{label} is not \"{str_val}\""
        elif op in ("is_one_of", "is_not_one_of"):
            clean_vals = [str(v).strip() for v in vals if str(v).strip()]
            if not clean_vals and val:
                clean_vals = [v.strip() for v in str(val).split(",") if v.strip()]
            if not clean_vals:
                raise ValueError(f"Operator '{op}' requires at least one selected value.")
            
            placeholders = ", ".join(["%s"] * len(clean_vals))
            joined_str = ", ".join(clean_vals)
            if op == "is_one_of":
                return f"{col} IN ({placeholders})", clean_vals, f"{label} is one of ({joined_str})"
            else:
                return f"({col} NOT IN ({placeholders}) OR {col} IS NULL)", clean_vals, f"{label} is not one of ({joined_str})"

    # 4. Numeric fields
    if data_type == "numeric":
        if op == "between":
            if val is None or val_to is None:
                raise ValueError("Between operator requires both minimum and maximum values.")
            n1 = _validate_numeric(val)
            n2 = _validate_numeric(val_to)
            low, high = min(n1, n2), max(n1, n2)
            return f"{col} BETWEEN %s AND %s", [low, high], f"{label} between {low} and {high}"
        
        num_val = _validate_numeric(val)
        op_map = {
            "equals": ("=", "equals"),
            "does_not_equal": ("!=", "does not equal"),
            "greater_than": (">", "greater than"),
            "less_than": ("<", "less than"),
            "greater_than_or_equal": (">=", "greater than or equal to"),
            "less_than_or_equal": ("<=", "less than or equal to"),
        }
        sql_sym, desc = op_map[op]
        if op == "does_not_equal":
            return f"({col} != %s OR {col} IS NULL)", [num_val], f"{label} {desc} {num_val}"
        return f"{col} {sql_sym} %s", [num_val], f"{label} {desc} {num_val}"

    # 5. Date fields
    if data_type == "date":
        if op == "between":
            if not val or not val_to:
                raise ValueError("Between operator requires both start date and end date.")
            d1 = _validate_date_str(str(val))
            d2 = _validate_date_str(str(val_to))
            d_start, d_end = min(d1, d2), max(d1, d2)
            return f"DATE({col}) BETWEEN %s AND %s", [d_start, d_end], f"{label} between {d_start} and {d_end}"

        d_val = _validate_date_str(str(val))
        date_op_map = {
            "is": ("=", "is"),
            "is_before": ("<", "is before"),
            "is_after": (">", "is after"),
            "is_on_or_before": ("<=", "is on or before"),
            "is_on_or_after": (">=", "is on or after"),
        }
        sql_sym, desc = date_op_map[op]
        return f"DATE({col}) {sql_sym} %s", [d_val], f"{label} {desc} {d_val}"

    raise ValueError(f"Unhandled condition for field '{field_key}' with operator '{op}'")


def build_filter_query(
    filter_groups: Optional[List[Dict[str, Any]]] = None,
    sort_by: Optional[List[Dict[str, str]]] = None,
    page: int = 1,
    per_page: int = 10,
    organization_id: Optional[str] = None,
) -> Tuple[str, str, List[Any], str]:
    """
    Build parameterized SQL queries for data fetching and counting.
    Returns:
        (data_sql, count_sql, parameters, readable_summary)
    """
    params: List[Any] = []
    top_clauses: List[str] = []
    summary_parts: List[str] = []

    # Enforce organization isolation if provided
    if organization_id:
        top_clauses.append("organization_id = %s")
        params.append(str(organization_id))
        summary_parts.append(f"Organization ID = {organization_id}")

    # Process filter groups
    if filter_groups:
        for g_idx, group in enumerate(filter_groups):
            raw_log_op = group.get("logical_operator", "AND").upper()
            log_op = "OR" if raw_log_op == "OR" else "AND"
            conditions = group.get("conditions", [])

            group_clauses: List[str] = []
            group_summaries: List[str] = []

            for cond in conditions:
                sql_frag, cond_params, cond_sum = build_condition_sql(cond)
                group_clauses.append(sql_frag)
                params.extend(cond_params)
                group_summaries.append(cond_sum)

            if group_clauses:
                glue = f" {log_op} "
                summary_glue = f" .{log_op.lower()}. "
                
                joined_group = glue.join(group_clauses)
                if len(group_clauses) > 1:
                    joined_group = f"({joined_group})"
                top_clauses.append(joined_group)

                joined_summary = summary_glue.join(group_summaries)
                if len(group_summaries) > 1 and len(filter_groups) > 1:
                    joined_summary = f"({joined_summary})"
                summary_parts.append(joined_summary)

    where_sql = ""
    if top_clauses:
        where_sql = "WHERE " + " AND ".join(top_clauses)

    readable_summary = "All"
    if summary_parts:
        readable_summary = "All > " + " .and. ".join(summary_parts)

    # Count query
    count_sql = f"SELECT COUNT(*) FROM submissions {where_sql}"

    # Sort query construction
    sort_clauses: List[str] = []
    if sort_by:
        for s in sort_by:
            s_field = s.get("field")
            if s_field and s_field in ALLOWED_SORT_FIELDS:
                col_name = ALLOWED_FILTER_FIELDS[s_field]["column"]
                dir_str = "ASC" if str(s.get("direction", "")).lower() == "asc" else "DESC"
                sort_clauses.append(f"{col_name} {dir_str} NULLS LAST")

    # Deterministic secondary fallback sort
    if not sort_clauses:
        sort_clauses = ["submitted_at DESC NULLS LAST", "id DESC"]
    elif "id" not in [s.get("field") for s in (sort_by or [])]:
        sort_clauses.append("id DESC")

    order_by_sql = "ORDER BY " + ", ".join(sort_clauses)

    # Pagination validation
    p = max(1, int(page))
    limit = max(1, min(100, int(per_page)))
    offset = (p - 1) * limit

    data_sql = f"""
        SELECT id, name, designation, company_name, email, contact_number, submitted_at,
               overall_avg, overall_level, status, answers,
               lc_score, ro_score, we_score, be_score,
               tm_score, ca_score, pc_score, sp_score
        FROM submissions
        {where_sql}
        {order_by_sql}
        LIMIT {limit} OFFSET {offset}
    """

    return data_sql, count_sql, params, readable_summary
