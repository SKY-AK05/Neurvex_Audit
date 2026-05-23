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

    q5: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q6: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q7: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q8: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q9: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q10: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q11: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q12: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q13: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q14: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q15: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q16: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q17: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q18: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q19: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q20: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q21: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q22: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q23: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q24: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q25: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q26: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q27: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q28: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q29: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q30: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q31: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q32: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q33: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q34: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q35: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q36: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q37: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q38: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q39: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q40: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q41: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q42: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q43: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
    q44: str = Field(..., pattern="^(Yes|Partially|No|Not Sure)$")
