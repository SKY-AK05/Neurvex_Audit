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

    # We will capture any additional questions dynamically
    class Config:
        extra = "allow"
