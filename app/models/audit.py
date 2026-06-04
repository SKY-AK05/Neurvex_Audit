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

    q5: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q6: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q7: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q8: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q9: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q10: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q11: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q12: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q13: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q14: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q15: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q16: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q17: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q18: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q19: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q20: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q21: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q22: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q23: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q24: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q25: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q26: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q27: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q28: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q29: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q30: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q31: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q32: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q33: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q34: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q35: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q36: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q37: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q38: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q39: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q40: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q41: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q42: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q43: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
    q44: str = Field(..., pattern="^(Yes|Partially|No|Not Sure|NA|)$")
