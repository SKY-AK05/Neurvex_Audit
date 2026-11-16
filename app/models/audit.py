"""
audit.py — Audit submission model
Mirrors the `submissions` table schema defined in create_table.sql.
"""
import re
from pydantic import BaseModel, Field, EmailStr, field_validator
from typing import Optional

class AuditSubmission(BaseModel):
    name: Optional[str] = Field(None, max_length=255)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v.strip():
            cleaned = v.strip()
            if not re.match(r"^[a-zA-Z0-9\u00C0-\u024F\u1E00-\u1EFF\s'\-\.]+$", cleaned):
                raise ValueError("Name contains invalid characters. Special characters such as @ are not allowed.")
            return cleaned
        return v
    designation: Optional[str] = Field(None, max_length=255)
    company_name: Optional[str] = Field(None, max_length=255)
    organization_id: Optional[str] = None
    invitation_token: Optional[str] = None
    t: Optional[str] = None
    access_token: Optional[str] = None
    campaign_id: Optional[str] = None
    email: EmailStr
    contact_number: Optional[str] = Field(None, max_length=50)
    consent_given: Optional[bool] = False
    draft_id: Optional[str] = None
    idempotency_key: Optional[str] = Field(None, max_length=64)

    # Demographic fields (Tell Us About You)
    function: Optional[str] = None
    function_other: Optional[str] = None
    role: Optional[str] = None
    country: Optional[str] = None
    state_ut: Optional[str] = None
    gender: Optional[str] = None
    gender_other: Optional[str] = None
    is_pwd: Optional[str] = None
    is_neurodivergent: Optional[str] = None
    is_marginalized: Optional[str] = None

    # Gating questions for Built Environment (section 4) and Suppliers (section 8)
    has_physical_workspace: Optional[str] = Field(None, pattern="^(Yes|No|)$")
    has_suppliers: Optional[str] = Field(None, pattern="^(Yes|No|)$")

    # We will capture any additional questions dynamically
    class Config:
        extra = "allow"
