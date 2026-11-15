# Domain & Pydantic Data Models

> Unit `05-models` · kind: feature

## Summary

Pydantic validation models, domain types, request payloads, and response serialization schemas.

## Context & goal

The Models unit provides strong schema definitions and runtime validation using Pydantic. It validates survey payloads, Likert ratings, dynamic questionnaire configurations, administrative actions, and user roles.

## User stories

- As a Backend Developer, I rely on Pydantic models to guarantee incoming HTTP requests conform to expected types before reaching service logic.
- As an API Consumer, I receive standardized, typed JSON response schemas across all endpoints.

## Functional requirements

- 1. Audit Submission Validation [confirmed]: Enforce 4 required demographic attributes and 40 Likert scores bounded between 1 and 5 inclusive.
- 2. Form Builder Models [confirmed]: Define `SectionCreate`, `QuestionUpdate`, and dependency schemas with validation rules.
- 3. User & Auth Schemas [confirmed]: Define `AdminUserResponse`, `UserCreateRequest`, and `RoleEnum` (`admin`, `super`).
- 4. Organization Schemas [confirmed]: Validate organization creation, invitation generation, and token management payloads.


## Interfaces & data

Defines data transfer objects for all endpoints in [INTERFACES.md](../../architecture/INTERFACES.md).
Reflects database entities in [DATA-MODEL.md](../../architecture/DATA-MODEL.md).

## Acceptance criteria

- Given an audit submission payload missing a demographic question, When validated by Pydantic, Then HTTP 422 Unprocessable Entity is raised.
- Given a Likert score value of 6, When submitted, Then Pydantic validation fails with value error 'Value must be between 1 and 5'.

## Edge cases & failure modes

- **Malformed JSON payload:** Handled by FastAPI Pydantic parser, returning structured error list detailing exact invalid fields.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Migrate from Pydantic V1 syntax to Pydantic V2 for 5x serialization performance gains.
- Generate OpenAPI TypeScript client models directly from Pydantic schemas.


## Source material

Key source for this unit (4 file(s) total, showing up to 15):

#### `app/models/__init__.py`

```python

```

#### `app/models/audit.py`

```python
"""
audit.py — Audit submission model
Mirrors the `submissions` table schema defined in create_table.sql.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional

class AuditSubmission(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
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

```

#### `app/models/form_builder.py`

```python
from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any

class QuestionBase(BaseModel):
    field_name: str
    short_title: str
    question_text: str
    order_index: int = 0
    depends_on_field: Optional[str] = None
    depends_on_value: Optional[str] = None
    score_mapping: Dict[str, int] = Field(
        default_factory=lambda: {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0, "N/A": 0}
    )

class QuestionCreate(QuestionBase):
    pass

class QuestionResponse(QuestionBase):
    id: int
    section_id: int

class SectionBase(BaseModel):
    section_code: str
    title: str
    icon: Optional[str] = None
    summary: Optional[str] = None
    why_it_matters: Optional[str] = None
    tip: Optional[str] = None
    gating_question: Optional[str] = None
    gating_field: Optional[str] = None
    order_index: int = 0

class SectionCreate(SectionBase):
    pass

class SectionResponse(SectionBase):
    id: int
    questions: List[QuestionResponse] = []

```

#### `app/models/user.py`

```python
"""
user.py — User/admin model
"""

```


## Improvements & refactors

- [keep-behavior] Formalize typing and input constraints for enhanced runtime validation.
- [keep-behavior] Expand automated test coverage for failure modes and timeouts.
- [keep-behavior] Optimize memory footprint and eliminate unreferenced legacy helpers.


## Definition of done

- [ ] Every functional requirement is implemented and covered by a test.
- [ ] Every acceptance-criteria scenario passes (including the failure paths).
- [ ] Every operation this unit owns in `architecture/INTERFACES.md` responds correctly.
- [ ] Every entity it writes matches `architecture/DATA-MODEL.md` (fields, types, constraints).
- [ ] Every write is satisfiable against the schema: no required (NOT NULL, no-default) column or foreign key is left unfilled; anonymous/public operations write only to anonymous-capable entities (no owner FK).
- [ ] Every enum/domain value this unit uses is one of the members fully enumerated in `architecture/DATA-MODEL.md`.
- [ ] Every edge case & failure mode above is handled.
- [ ] `node scripts/analyze.mjs --check --out <out>` passes — no unresolved agent callouts or placeholders, and every reference resolves.

