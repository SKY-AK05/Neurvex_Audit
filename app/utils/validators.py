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
