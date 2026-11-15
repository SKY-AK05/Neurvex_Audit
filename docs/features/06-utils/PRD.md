# Utility Functions, Formatting & Cryptography

> Unit `06-utils` · kind: feature

## Summary

CSV report generation, token generation, cryptographic validation, and branded HTML email formatting.

## Context & goal

The Utils unit contains shared stateless utilities. It provides CSV export formatting for survey submissions, cryptographically secure random token generation for invitation and resumption links, email address syntax verification, and responsive HTML email template compilation.

## User stories

- As an Organization Admin, I can export aggregated survey submissions into a well-formatted CSV file.
- As a Survey Respondent, I receive an aesthetically designed HTML email scorecard highlighting my organization's inclusion results.
- As a Security Engineer, I rely on cryptographically secure random tokens to prevent token enumeration attacks.

## Functional requirements

- 1. CSV Generation [confirmed]: Generate RFC 4180 compliant CSV exports with proper escaping of commas and special characters.
- 2. Secure Token Generation [confirmed]: Use Python `secrets` module to generate high-entropy alphanumeric access and invitation tokens.
- 3. Branded HTML Email Template [confirmed]: Compile responsive HTML email containing score breakdown, maturity tier badges, and Orchvate action steps.
- 4. Email Policy Validation [confirmed]: Validate corporate domain syntaxes and prevent disposable email domains where corporate audits are required.


## Interfaces & data

Referenced by `app/services/export_service.py` and `app/services/scoring_service.py`.
Outputs HTML email payloads dispatched via Azure Communication Services.

## Acceptance criteria

- Given a list of 100 submissions, When CSV exporter runs, Then a valid CSV byte stream with header row and 100 data rows is produced.
- Given an invitation token generation request, When generated, Then a 32-character URL-safe cryptographic token is returned.
- Given an email generation call, When compiled, Then HTML contains valid CSS matching the NIWI Design System tokens.

## Edge cases & failure modes

- **CSV injection risks:** Fields starting with `=`, `+`, `-`, or `@` are sanitized with leading single quotes to prevent spreadsheet formula injection.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Migrate string formatting in HTML emails to Jinja2 template engine.
- Add automated visual regression testing for email templates across Outlook and Gmail clients.


## Source material

Key source for this unit (4 file(s) total, showing up to 15):

#### `app/utils/__init__.py`

```python

```

#### `app/utils/helpers.py`

```python
"""
helpers.py — General utility functions
"""
from datetime import datetime, timezone, timedelta

IST = timezone(timedelta(hours=5, minutes=30))


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def now_ist() -> datetime:
    return datetime.now(IST)


def to_iso_utc(dt: datetime | None) -> str | None:
    """Serialize datetimes for JSON (always UTC with Z suffix)."""
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def safe_isoformat(dt) -> str | None:
    if dt is None:
        return None
    if isinstance(dt, datetime):
        return to_iso_utc(dt)
    return str(dt)

```

#### `app/utils/logger.py`

```python
"""
logger.py — Centralised logging setup
"""
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)

def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)

```

#### `app/utils/validators.py`

```python
"""
validators.py — Input validation helpers
"""

REQUIRED_RESPONDENT_FIELDS = ("name", "company_name", "email")
QUESTION_FIELDS = [f"q{i}" for i in range(5, 45)]
VALID_ANSWERS = {"Yes", "Partially", "No", "Not Sure"}


def validate_submission(data: dict) -> list[str]:
    """Returns a list of validation error messages, empty if valid."""
    errors = []
    for field in REQUIRED_RESPONDENT_FIELDS:
        if not data.get(field):
            errors.append(f"Missing required field: {field}")
    for q in QUESTION_FIELDS:
        val = data.get(q)
        if val not in VALID_ANSWERS:
            errors.append(f"Invalid or missing answer for {q}: '{val}'")
    return errors

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

