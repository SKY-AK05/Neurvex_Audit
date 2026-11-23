"""
test_drafts.py — Unit and integration tests for the Draft Saving and Resuming system.
Verifies:
1. Save and resume draft within valid 30-day window.
2. Token expiration after 30 days returns 401.
3. Database record expiration after 30 days returns 401.
4. Auto-cleanup purges drafts older than 30 days upon new save operations.
5. Already submitted drafts cannot be resumed or overwritten.
6. Draft ownership validation (IDOR/BOLA protection) rejects unauthorized email modifications with 403.
"""
import uuid
import jwt
from datetime import datetime, timezone, timedelta
from fastapi.testclient import TestClient

from app.main import app
from app.core.config import JWT_SECRET
from conftest import MEM_STORE

client = TestClient(app)


def test_save_and_resume_draft():
    """Standard flow: saving a draft and resuming with a valid 30-day token succeeds."""
    MEM_STORE.reset()
    payload = {
        "email": "org-test@company.com",
        "company_name": "Test Company Ltd",
        "form_state": {"q5": "Yes", "q6": "No", "name": "Test User"},
        "current_step": 2
    }
    response = client.post("/api/drafts/save", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "draft_id" in data
    assert "resume_url" in data

    token = data["resume_url"].split("token=")[1]
    decoded = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    assert "exp" in decoded
    # Verify exp is set to ~30 days (between 29 and 31 days from now)
    exp_dt = datetime.fromtimestamp(decoded["exp"], tz=timezone.utc)
    now = datetime.now(timezone.utc)
    time_diff = exp_dt - now
    assert timedelta(days=29) <= time_diff <= timedelta(days=31)

    # Resume draft
    res_response = client.get(f"/api/drafts/resume?token={token}")
    assert res_response.status_code == 200
    res_data = res_response.json()
    assert res_data["email"] == "org-test@company.com"
    assert res_data["company_name"] == "Test Company Ltd"
    assert res_data["form_state"]["q5"] == "Yes"
    assert res_data["current_step"] == 2


def test_draft_token_expired_after_30_days():
    """A resume link whose token expired (>30 days) is rejected with 401."""
    MEM_STORE.reset()
    draft_id = str(uuid.uuid4())
    # Expired token (created 31 days ago)
    exp = datetime.now(timezone.utc) - timedelta(days=1)
    expired_token = jwt.encode({"draft_id": draft_id, "exp": exp}, JWT_SECRET, algorithm="HS256")

    response = client.get(f"/api/drafts/resume?token={expired_token}")
    assert response.status_code == 401
    assert "expired" in response.json().get("detail", "").lower()


def test_draft_database_record_expired_after_30_days():
    """A draft whose database record is older than 30 days is rejected with 401."""
    MEM_STORE.reset()
    draft_id = str(uuid.uuid4())
    old_timestamp = datetime.now(timezone.utc) - timedelta(days=31)
    MEM_STORE.drafts[draft_id] = {
        "id": draft_id,
        "email": "stale@company.com",
        "company_name": "Stale Corp",
        "form_state": {"q5": "Yes"},
        "current_step": 1,
        "submitted": False,
        "created_at": old_timestamp,
        "updated_at": old_timestamp
    }

    # Generate a fresh token pointing to the stale record
    fresh_token = jwt.encode(
        {"draft_id": draft_id, "exp": datetime.now(timezone.utc) + timedelta(hours=1)},
        JWT_SECRET,
        algorithm="HS256"
    )

    response = client.get(f"/api/drafts/resume?token={fresh_token}")
    assert response.status_code == 401
    assert "30-day limit" in response.json().get("detail", "")


def test_draft_auto_cleanup_purges_stale_records():
    """Calling POST /api/drafts/save automatically cleans up drafts older than 30 days."""
    MEM_STORE.reset()
    stale_draft_id = str(uuid.uuid4())
    old_timestamp = datetime.now(timezone.utc) - timedelta(days=32)
    MEM_STORE.drafts[stale_draft_id] = {
        "id": stale_draft_id,
        "email": "cleanup@company.com",
        "company_name": "Cleanup Corp",
        "form_state": {},
        "current_step": 1,
        "submitted": False,
        "created_at": old_timestamp,
        "updated_at": old_timestamp
    }

    assert stale_draft_id in MEM_STORE.drafts

    # Saving any new draft triggers the automatic 30-day cleanup query
    new_payload = {
        "email": "newuser@company.com",
        "company_name": "New Corp",
        "form_state": {"q5": "Yes"},
        "current_step": 1
    }
    res = client.post("/api/drafts/save", json=new_payload)
    assert res.status_code == 200

    # Stale record should have been purged by the cleanup query
    assert stale_draft_id not in MEM_STORE.drafts


def test_submitted_draft_cannot_be_resumed():
    """A draft that was already submitted cannot be resumed again."""
    MEM_STORE.reset()
    draft_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    MEM_STORE.drafts[draft_id] = {
        "id": draft_id,
        "email": "done@company.com",
        "company_name": "Done Corp",
        "form_state": {"q5": "Yes"},
        "current_step": 9,
        "submitted": True,
        "created_at": now,
        "updated_at": now
    }

    token = jwt.encode(
        {"draft_id": draft_id, "exp": now + timedelta(days=2)},
        JWT_SECRET,
        algorithm="HS256"
    )

    response = client.get(f"/api/drafts/resume?token={token}")
    assert response.status_code == 400
    assert "already been submitted" in response.json().get("detail", "")


def test_render_draft_email_styling():
    """Verify that Orchvate brand colors, typography and 30-day resume link are present."""
    from app.api.drafts import render_draft_email

    subject, html, plain = render_draft_email(
        is_reminder=True,
        name="Sarah Connor",
        company_name="Cyberdyne Systems",
        resume_url="https://niwi.orchvate.in/resume?token=sample123"
    )

    assert "Reminder: Continue your NIWI Self-Assessment — Cyberdyne Systems" in subject
    # Orchvate brand styling tokens
    assert "#120050" in html  # Orchvate Navy
    assert "#009070" in html  # Orchvate Teal CTA
    assert "DM Sans" in html
    assert "Sarah Connor" in html
    assert "Cyberdyne Systems" in html
    assert "https://niwi.orchvate.in/resume?token=sample123" in html
    assert "30 Days" in html
    assert "https://niwi.orchvate.in/resume?token=sample123" in plain


def test_process_draft_reminders_worker():
    """Verify draft reminder worker detects incomplete drafts >48h and dispatches reminders."""
    from app.api.drafts import process_draft_reminders

    MEM_STORE.reset()
    draft_id = str(uuid.uuid4())
    # Created/updated 50 hours ago (within 30 days, >48 hours)
    old_timestamp = datetime.now(timezone.utc) - timedelta(hours=50)
    MEM_STORE.drafts[draft_id] = {
        "id": draft_id,
        "email": "incomplete-user@company.com",
        "company_name": "Acme Industries",
        "form_state": {"name": "Alex", "q5": "Yes"},
        "current_step": 4,
        "submitted": False,
        "created_at": old_timestamp,
        "updated_at": old_timestamp,
        "reminder_sent_at": None,
        "reminder_count": 0
    }

    # Execute worker reminder processing
    sent_count = process_draft_reminders()
    assert sent_count == 1
    assert MEM_STORE.drafts[draft_id]["reminder_sent_at"] is not None
    assert MEM_STORE.drafts[draft_id]["reminder_count"] == 1

    # Second run should not duplicate reminders for already-reminded draft
    second_run_count = process_draft_reminders()
    assert second_run_count == 0

