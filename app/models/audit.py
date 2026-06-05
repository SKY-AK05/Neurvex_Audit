"""
audit.py — Audit submission model
Mirrors the `submissions` table schema defined in create_table.sql.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class AuditSubmission(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    designation: str = Field(..., min_length=2, max_length=255)
    company_name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    contact_number: Optional[str] = Field(None, max_length=50)
    consent_given: Optional[bool] = False
    draft_id: Optional[str] = None

    # Gating questions for Built Environment (section 4) and Suppliers (section 8)
    has_physical_workspace: Optional[str] = Field(None, pattern="^(Yes|No|)$")
    has_suppliers: Optional[str] = Field(None, pattern="^(Yes|No|)$")

    q5: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q6: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q7: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q8: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q9: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q10: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q11: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q12: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q13: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q14: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q15: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q16: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q17: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q18: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q19: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q20: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q21: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q22: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q23: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q24: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q25: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q26: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q27: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q28: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q29: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q30: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q31: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q32: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q33: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q34: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q35: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q36: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q37: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q38: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q39: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q40: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q41: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q42: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q43: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
    q44: Optional[str] = Field("", pattern="^(Yes|Partially|No|Not Sure|N/A|NA|)$")
