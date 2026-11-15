# REST API Routing & Controller Layer

> Unit `08-api` · kind: feature

## Summary

FastAPI routers for survey submission, organization management, admin operations, invitations, drafts, and telemetry.

## Context & goal

The API unit implements the external HTTP interface of NIWI. It exposes public survey ingestion (`/api/submit`), client-side draft auto-save (`/api/drafts/*`), public link resolution (`/api/public/*`), administrative executive portals (`/api/admin/*`, `/api/manage/*`), and system telemetry (`/api/health/*`).

## User stories

- As an Audit Respondent, I submit my survey and receive instant acknowledgement within 25ms.
- As an Organization Admin, I create and manage participation invitation links.
- As a Super Admin, I monitor dead-letter queues and replay failed submissions with a single API call.

## Functional requirements

- 1. Sub-25ms Asynchronous Ingestion [confirmed]: Respond with HTTP 202 Accepted and `submission_id` upon successful outbox write.
- 2. Public Link & Invitation Resolution [confirmed]: Validate tokens and resolve associated organization metadata without requiring authentication.
- 3. Draft Management [confirmed]: Save and resume in-progress assessments via secure resume tokens.
- 4. Admin Dashboard Metrics [confirmed]: Return aggregated completion statistics, pillar averages, and recent activity logs.
- 5. Dead-Letter Queue Operations [confirmed]: Expose endpoints to list failed outbox messages and trigger single or bulk replays.


## Routes

| Method | Route | Kind | File |
| --- | --- | --- | --- |
| GET | `/api/admin/dashboard` | api | `app/api/routes.py:2028` |
| GET | `/api/admin/submissions/dead-lettered` | api | `app/api/routes.py:1852` |
| POST | `/api/admin/submissions/dead-lettered/replay-all` | api | `app/api/routes.py:1965` |
| POST | `/api/admin/submissions/{submission_id}/replay` | api | `app/api/routes.py:1897` |
| GET | `/api/auth/config` | api | `app/api/routes.py:1669` |
| POST | `/api/auth/verify` | api | `app/api/routes.py:1682` |
| POST | `/api/book-call` | api | `app/api/routes.py:1535` |
| GET | `/api/drafts/resume` | api | `app/api/drafts.py:146` |
| POST | `/api/drafts/save` | api | `app/api/drafts.py:95` |
| DELETE | `/api/form/questions/{question_id}` | api | `app/api/form_builder.py:250` |
| PUT | `/api/form/questions/{question_id}` | api | `app/api/form_builder.py:221` |
| GET | `/api/form/sections` | api | `app/api/form_builder.py:106` |
| POST | `/api/form/sections` | api | `app/api/form_builder.py:136` |
| DELETE | `/api/form/sections/{section_id}` | api | `app/api/form_builder.py:182` |
| PUT | `/api/form/sections/{section_id}` | api | `app/api/form_builder.py:157` |
| POST | `/api/form/sections/{section_id}/questions` | api | `app/api/form_builder.py:200` |
| GET | `/api/health` | api | `app/main.py:124` |
| GET | `/api/health/cache-metrics` | api | `app/main.py:161` |
| GET | `/api/health/pool-metrics` | api | `app/main.py:154` |
| GET | `/api/manage/audit-logs` | api | `app/api/routes.py:1825` |
| GET | `/api/manage/orgs` | api | `app/api/orgs.py:125` |
| POST | `/api/manage/orgs` | api | `app/api/orgs.py:240` |
| POST | `/api/manage/orgs/create` | api | `app/api/orgs.py:307` |
| PATCH | `/api/manage/orgs/invitations/{invitation_id}` | api | `app/api/orgs.py:724` |
| POST | `/api/manage/orgs/invitations/{invitation_id}/regenerate` | api | `app/api/orgs.py:786` |
| POST | `/api/manage/orgs/invitations/{invitation_id}/revoke` | api | `app/api/orgs.py:759` |
| GET | `/api/manage/orgs/unlinked` | api | `app/api/orgs.py:322` |
| DELETE | `/api/manage/orgs/{org_id}` | api | `app/api/orgs.py:482` |
| GET | `/api/manage/orgs/{org_id}` | api | `app/api/orgs.py:360` |
| PUT | `/api/manage/orgs/{org_id}` | api | `app/api/orgs.py:395` |
| GET | `/api/manage/orgs/{org_id}/assessment-links` | api | `app/api/orgs.py:605` |
| POST | `/api/manage/orgs/{org_id}/assessment-links` | api | `app/api/orgs.py:561` |
| POST | `/api/manage/orgs/{org_id}/assessment-links/default` | api | `app/api/orgs.py:585` |
| DELETE | `/api/manage/orgs/{org_id}/assessment-links/{token_id}` | api | `app/api/orgs.py:632` |
| GET | `/api/manage/orgs/{org_id}/invitations` | api | `app/api/orgs.py:702` |
| POST | `/api/manage/orgs/{org_id}/invitations` | api | `app/api/orgs.py:652` |
| POST | `/api/manage/orgs/{org_id}/link` | api | `app/api/orgs.py:886` |
| PUT | `/api/manage/orgs/{org_id}/links/{submission_id}` | api | `app/api/orgs.py:845` |
| POST | `/api/manage/orgs/{org_id}/message` | api | `app/api/orgs.py:966` |
| GET | `/api/manage/orgs/{org_id}/report-preview` | api | `app/api/orgs.py:935` |
| POST | `/api/manage/orgs/{org_id}/restore` | api | `app/api/orgs.py:526` |
| PATCH | `/api/manage/orgs/{org_id}/status` | api | `app/api/orgs.py:444` |
| GET | `/api/manage/settings/rate-limits` | api | `app/api/routes.py:1480` |
| PUT | `/api/manage/settings/rate-limits` | api | `app/api/routes.py:1491` |
| POST | `/api/manage/settings/rate-limits/reset` | api | `app/api/routes.py:1516` |
| GET | `/api/manage/users` | api | `app/api/routes.py:1706` |
| POST | `/api/manage/users` | api | `app/api/routes.py:1721` |
| DELETE | `/api/manage/users/{email}` | api | `app/api/routes.py:1748` |
| GET | `/api/org/dashboard` | api | `app/api/org.py:140` |
| POST | `/api/org/register` | api | `app/api/org.py:27` |
| GET | `/api/org/verify` | api | `app/api/org.py:67` |
| POST | `/api/public/assessment/resolve-legacy-org` | api | `app/api/public.py:65` |
| POST | `/api/public/assessment/resolve-link` | api | `app/api/public.py:46` |
| POST | `/api/public/email/validate` | api | `app/api/public.py:100` |
| POST | `/api/public/invitations/validate` | api | `app/api/public.py:150` |
| POST | `/api/public/organisations/validate` | api | `app/api/public.py:110` |
| GET | `/api/settings` | api | `app/api/routes.py:1409` |
| PUT | `/api/settings` | api | `app/api/routes.py:1422` |
| POST | `/api/settings/delete-all-records` | api | `app/api/routes.py:1767` |
| POST | `/api/settings/notifications/toggle` | api | `app/api/routes.py:1449` |
| GET | `/api/settings/rate-limits` | api | `app/api/routes.py:1481` |
| PUT | `/api/settings/rate-limits` | api | `app/api/routes.py:1492` |
| POST | `/api/settings/rate-limits/reset` | api | `app/api/routes.py:1517` |
| GET | `/api/submissions` | api | `app/api/routes.py:404` |
| POST | `/api/submissions/filter` | api | `app/api/routes.py:506` |
| GET | `/api/submissions/saved-filters` | api | `app/api/routes.py:645` |
| POST | `/api/submissions/saved-filters` | api | `app/api/routes.py:685` |
| DELETE | `/api/submissions/saved-filters/{filter_id}` | api | `app/api/routes.py:736` |
| GET | `/api/submissions/{submission_id}` | api | `app/api/routes.py:883` |
| PUT | `/api/submissions/{submission_id}/email` | api | `app/api/routes.py:1210` |
| PATCH | `/api/submissions/{submission_id}/organisation` | api | `app/api/routes.py:1091` |
| POST | `/api/submissions/{submission_id}/regenerate-email` | api | `app/api/routes.py:1247` |
| PATCH | `/api/submissions/{submission_id}/respondent` | api | `app/api/routes.py:957` |
| PATCH | `/api/submissions/{submission_id}/scores` | api | `app/api/routes.py:998` |
| POST | `/api/submissions/{submission_id}/send` | api | `app/api/routes.py:1352` |
| GET | `/api/submissions/{submission_id}/status` | api | `app/api/routes.py:763` |
| POST | `/api/submit` | api | `app/api/routes.py:129` |
| POST | `/api/support` | api | `app/api/routes.py:1630` |

## Interfaces & data

Implements all 80 routes specified in [INTERFACES.md](../../architecture/INTERFACES.md).
Secured by Bearer JWT middleware and SlowAPI rate limiting.

## Acceptance criteria

- Given a valid survey payload with Idempotency-Key header, When `POST /api/submit` is called, Then HTTP 202 is returned in under 25ms.
- Given an administrator request to replay a dead-lettered submission, When `POST /api/admin/submissions/{id}/replay` is called, Then the message status resets to 'pending'.
- Given an invalid resume token, When `GET /api/drafts/resume` is called, Then HTTP 404 Not Found is returned.

## Edge cases & failure modes

- **Network disconnect during submission:** Client retries with identical Idempotency-Key; backend returns HTTP 202 without creating duplicate database rows.
- **Payload size exceeding limits:** SlowAPI / Starlette body limits reject oversized JSON with HTTP 413.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Generate OpenAPI v3 Swagger UI documentation with full interactive request mocking.
- Add ETags and HTTP caching headers on static metadata endpoints.


## Source material

Key source for this unit (8 file(s) total, showing up to 15):

#### `app/api/__init__.py`

```python

```

#### `app/api/auth.py`

```python
"""
auth.py — Authentication helpers
Handles admin password verification and session management.
"""

```

#### `app/api/drafts.py`

```python
import os
import json
import logging
from datetime import datetime, timezone, timedelta
from uuid import UUID
import jwt
from pydantic import BaseModel, EmailStr
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request, BackgroundTasks

from app.core.database import get_db_connection
from app.services.settings_service import get_sender_for_send, send_acs_email

router = APIRouter(prefix="/drafts", tags=["Drafts"])
logger = logging.getLogger(__name__)

from app.core.config import JWT_SECRET, FRONTEND_URL

class SaveDraftPayload(BaseModel):
    draft_id: Optional[UUID] = None
    email: EmailStr
    company_name: str
    form_state: Dict[str, Any]
    current_step: int

def send_resume_email(email: str, name: str, company_name: str, resume_url: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
    except Exception as e:
        logger.error(f"Failed to load email settings for resume draft email: {e}")
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    if not sender_address:
        logger.error("No sender address configured for resume draft email")
        return

    subject = f"Resume your NeuroMark Inclusion Audit — {company_name}"
    plain = (
        f"Hi {name},\n\n"
        f"Your progress on the NeuroMark Inclusion Audit for {company_name} has been saved.\n\n"
        f"You can resume your audit anytime within the next 7 days by clicking the link below:\n"
        f"{resume_url}\n\n"
        f"Best regards,\n"
        f"The Orchvate Team\n"
    )
    
    html = f"""<!DOCTYPE html>
<html>
<head>
  <style>
    body {{ font-family: 'Inter', sans-serif; background-color: #F5F2EB; color: #120050; padding: 2rem; margin: 0; }}
    .card {{ background-color: #FFFFFF; border: 2px solid #120050; border-radius: 12px; padding: 2.5rem; max-width: 500px; margin: 0 auto; box-shadow: 4px 4px 0 #009070; }}
    h2 {{ font-family: 'Playfair Display', serif; font-size: 1.6rem; color: #120050; margin-top: 0; margin-bottom: 1rem; }}
    p {{ font-size: 0.95rem; line-height: 1.6; color: #555; margin-bottom: 1.5rem; }}
    .btn {{ display: inline-block; background-color: #120050; color: #FFFFFF !important; text-decoration: none; padding: 0.8rem 1.8rem; border-radius: 99px; font-weight: bold; border: 2px solid #120050; font-family: 'Playfair Display', serif; box-shadow: 3px 3px 0 #C8F31D; margin-top: 0.5rem; }}
    .btn:hover {{ background-color: #009070; border-color: #009070; box-shadow: 3px 3px 0 #120050; }}
    .footer {{ font-size: 0.8rem; color: #aaa; margin-top: 2rem; text-align: center; border-top: 1px solid #E2DDD4; padding-top: 1rem; }}
  </style>
</head>
<body>
  <div class="card">
    <h2>Audit Progress Saved</h2>
    <p>Hi {name or 'there'},</p>
    <p>Your progress on the NeuroMark Inclusion Audit for <strong>{company_name}</strong> has been saved.</p>
    <p>You can resume your audit anytime within the next 7 days by clicking the button below:</p>
    <p style="text-align: center;">
      <a href="{resume_url}" class="btn">Resume Audit &rarr;</a>
    </p>
    <p>Or copy and paste this link into your browser:<br>
    <a href="{resume_url}" style="color: #009070;">{resume_url}</a></p>
    <div class="footer">
      <p>Powered by Orchvate</p>
    </div>
  </div>
</body>
</html>"""

    try:
        send_acs_email(
            to_address=email,
            to_name=name,
            subject=subject,
            html=html,
            plain=plain,
            sender_address=sender_address,
            sender_name=sender_name,
        )
        logger.info(f"Resume email sent to {email}")
    except Exception as e:
        logger.error(f"Failed to send resume email to {email}: {e}")

@router.post("/save")
async def save_draft(payload: SaveDraftPayload, request: Request, background_tasks: BackgroundTasks):
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    if payload.draft_id:
                        cur.execute("SELECT submitted FROM draft_submissions WHERE id = %s", (str(payload.draft_id),))
                        row = cur.fetchone()
                        if row and row[0]:
                            raise HTTPException(status_code=400, detail="This draft has already been submitted.")
                        
                        cur.execute("""
                            UPDATE draft_submissions
                            SET email = %s, company_name = %s, form_state = %s, current_step = %s, updated_at = NOW()
                            WHERE id = %s
                            RETURNING id
                        """, (payload.email, payload.company_name, json.dumps(payload.form_state), payload.current_step, str(payload.draft_id)))
                        draft_id = cur.fetchone()[0]
                    else:
                        cur.execute("""
                            INSERT INTO draft_submissions (email, company_name, form_state, current_step)
                            VALUES (%s, %s, %s, %s)
                            RETURNING id
                        """, (payload.email, payload.company_name, json.dumps(payload.form_state), payload.current_step))
                        draft_id = cur.fetchone()[0]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving draft: {e}")
        raise HTTPException(status_code=500, detail="Database save failed.")

    exp = datetime.now(timezone.utc) + timedelta(days=7)
    token = jwt.encode({"draft_id": str(draft_id), "exp": exp}, JWT_SECRET, algorithm="HS256")
    
    resume_url = f"{FRONTEND_URL}/resume?token={token}"
    
    background_tasks.add_task(
        send_resume_email,
        payload.email,
        payload.form_state.get("name", "there"),
        payload.company_name,
        resume_url
    )
    
    return {
        "success": True,
        "draft_id": str(draft_id),
        "resume_url": resume_url
    }

@router.get("/resume")
async def resume_draft(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        draft_id = payload.get("draft_id")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid resume token.")

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT email, company_name, form_state, current_step, submitted 
                    FROM draft_submissions WHERE id = %s
                """, (draft_id,))
                row = cur.fetchone()
    except Exception as e:
        logger.error(f"Database error while loading draft: {e}")
        raise HTTPException(status_code=500, detail="Database query failed.")

    if not row:
        raise HTTPException(status_code=404, detail="Draft not found.")
    
    email, company_name, form_state, current_step, submitted = row
    if submitted:
        raise HTTPException(status_code=400, detail="This draft has already been submitted.")

    return {
        "email": email,
        "company_name": company_name,
        "form_state": form_state,
        "current_step": current_step,
        "draft_id": draft_id
    }

```

#### `app/api/form_builder.py`

```python
import time
import threading
import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
import json
from app.core.database import get_db_connection, get_conn
from app.core.authorization import require_admin
from app.models.form_builder import SectionCreate, SectionResponse, QuestionCreate, QuestionResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory process-local cache for form sections
_cached_sections: Optional[List[dict]] = None
_cached_sections_time: float = 0.0
_SECTIONS_CACHE_TTL: float = 300.0  # 5 minutes
_cache_lock = threading.Lock()


def invalidate_form_sections_cache():
    """Invalidate process-local form sections cache on administrative mutation."""
    global _cached_sections, _cached_sections_time
    with _cache_lock:
        _cached_sections = None
        _cached_sections_time = 0.0
    logger.info("Form sections cache invalidated")
    
    # Also invalidate scoring_service cache to keep scoring in sync with admin edits
    try:
        from app.services import scoring_service
        if hasattr(scoring_service, "_cached_form_sections"):
            scoring_service._cached_form_sections = None
            scoring_service._cached_form_sections_time = 0
            logger.info("Scoring service sections cache invalidated")
    except Exception as e:
        logger.warning("Could not invalidate scoring service cache: %s", e)


def fetch_sections_from_db() -> List[dict]:
    """Execute a single query with LEFT JOIN and json_agg to retrieve all sections and questions."""
    conn = get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    s.id,
                    s.section_code,
                    s.title,
                    s.icon,
                    s.summary,
                    s.why_it_matters,
                    s.tip,
                    s.gating_question,
                    s.gating_field,
                    s.order_index,
                    COALESCE(
                        json_agg(
                            json_build_object(
                                'id', q.id,
                                'section_id', q.section_id,
                                'field_name', q.field_name,
                                'short_title', q.short_title,
                                'question_text', q.question_text,
                                'order_index', q.order_index,
                                'score_mapping', q.score_mapping,
                                'depends_on_field', q.depends_on_field,
                                'depends_on_value', q.depends_on_value
                            ) ORDER BY q.order_index ASC
                        ) FILTER (WHERE q.id IS NOT NULL),
                        '[]'::json
                    ) AS questions
                FROM form_sections s
                LEFT JOIN form_questions q ON s.id = q.section_id
                GROUP BY s.id
                ORDER BY s.order_index ASC;
            """)
            rows = cur.fetchall()
            sections = []
            for r in rows:
                questions_data = r[10]
                if isinstance(questions_data, str):
                    try:
                        questions_data = json.loads(questions_data)
                    except Exception:
                        questions_data = []
                sections.append({
                    "id": r[0],
                    "section_code": r[1],
                    "title": r[2],
                    "icon": r[3],
                    "summary": r[4],
                    "why_it_matters": r[5],
                    "tip": r[6],
                    "gating_question": r[7],
                    "gating_field": r[8],
                    "order_index": r[9],
                    "questions": questions_data
                })
            return sections
    finally:
        conn.close()


@router.get("/sections", response_model=List[SectionResponse])
def get_all_sections():
    global _cached_sections, _cached_sections_time
    now = time.time()
    
    # Fast path: cache hit without lock or database checkout
    if _cached_sections is not None and (now - _cached_sections_time) < _SECTIONS_CACHE_TTL:
        return _cached_sections
    
    # Cache miss or expired: use lock to prevent thundering herd
    with _cache_lock:
        # Double-check inside lock
        now = time.time()
        if _cached_sections is not None and (now - _cached_sections_time) < _SECTIONS_CACHE_TTL:
            return _cached_sections
        
        try:
            fresh_sections = fetch_sections_from_db()
            _cached_sections = fresh_sections
            _cached_sections_time = now
            return _cached_sections
        except Exception as e:
            logger.error("Failed to fetch form sections from DB: %s", e)
            # Stale-while-revalidate: if DB fails, return previous cache if available
            if _cached_sections is not None:
                logger.warning("Serving stale form sections from cache following DB error")
                return _cached_sections
            raise HTTPException(status_code=500, detail="Failed to load form sections")


@router.post("/sections", response_model=SectionResponse)
def create_section(section: SectionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO form_sections (section_code, title, icon, summary, why_it_matters, tip, gating_question, gating_field, order_index)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    section.section_code, section.title, section.icon, section.summary, 
                    section.why_it_matters, section.tip, section.gating_question, section.gating_field, section.order_index
                ))
                section_id = cur.fetchone()[0]
                conn.commit()
                invalidate_form_sections_cache()
                return {**section.dict(), "id": section_id, "questions": []}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.put("/sections/{section_id}", response_model=SectionResponse)
def update_section(section_id: int, section: SectionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE form_sections 
                    SET section_code=%s, title=%s, icon=%s, summary=%s, why_it_matters=%s, tip=%s, gating_question=%s, gating_field=%s, order_index=%s
                    WHERE id=%s
                """, (
                    section.section_code, section.title, section.icon, section.summary, 
                    section.why_it_matters, section.tip, section.gating_question, section.gating_field, section.order_index, section_id
                ))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Section not found")
                conn.commit()
                invalidate_form_sections_cache()
                return {**section.dict(), "id": section_id, "questions": []}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/sections/{section_id}")
def delete_section(section_id: int, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM form_sections WHERE id=%s", (section_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Section not found")
                conn.commit()
                invalidate_form_sections_cache()
                return {"message": "Section deleted"}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.post("/sections/{section_id}/questions", response_model=QuestionResponse)
def create_question(section_id: int, question: QuestionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO form_questions (section_id, field_name, short_title, question_text, order_index, score_mapping, depends_on_field, depends_on_value)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id
                """, (
                    section_id, question.field_name, question.short_title, question.question_text, 
                    question.order_index, json.dumps(question.score_mapping), question.depends_on_field, question.depends_on_value
                ))
                q_id = cur.fetchone()[0]
                conn.commit()
                invalidate_form_sections_cache()
                return {**question.dict(), "id": q_id, "section_id": section_id}
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.put("/questions/{question_id}", response_model=QuestionResponse)
def update_question(question_id: int, question: QuestionCreate, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT section_id FROM form_questions WHERE id=%s", (question_id,))
                row = cur.fetchone()
                if not row:
                    raise HTTPException(status_code=404, detail="Question not found")
                section_id = row[0]
                
                cur.execute("""
                    UPDATE form_questions 
                    SET field_name=%s, short_title=%s, question_text=%s, order_index=%s, score_mapping=%s, depends_on_field=%s, depends_on_value=%s
                    WHERE id=%s
                """, (
                    question.field_name, question.short_title, question.question_text, 
                    question.order_index, json.dumps(question.score_mapping), question.depends_on_field, question.depends_on_value, question_id
                ))
                conn.commit()
                invalidate_form_sections_cache()
                return {**question.dict(), "id": question_id, "section_id": section_id}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

@router.delete("/questions/{question_id}")
def delete_question(question_id: int, user: dict = Depends(require_admin)):
    with get_db_connection() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM form_questions WHERE id=%s", (question_id,))
                if cur.rowcount == 0:
                    raise HTTPException(status_code=404, detail="Question not found")
                conn.commit()
                invalidate_form_sections_cache()
                return {"message": "Question deleted"}
        except HTTPException:
            conn.rollback()
            raise
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=str(e))

```

#### `app/api/org.py`

```python
import os
import logging
import jwt
import psycopg2.extras
from datetime import datetime, timezone, timedelta
from uuid import UUID
from pydantic import BaseModel, EmailStr
from fastapi import APIRouter, HTTPException, Request, Depends

from app.core.database import get_db_connection
from app.services.settings_service import send_acs_email, get_sender_for_send

router = APIRouter(prefix="/org", tags=["Organizations"])
logger = logging.getLogger(__name__)

from app.core.config import JWT_SECRET, FRONTEND_URL
from app.utils.helpers import to_iso_utc

class RegisterPayload(BaseModel):
    email: EmailStr
    company_name: str

def create_magic_link_token(email: str, company_name: str) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=15)
    return jwt.encode({"email": email.lower(), "company_name": company_name, "exp": exp, "type": "magic_link"}, JWT_SECRET, algorithm="HS256")

@router.post("/register")
async def register_or_login_org(payload: RegisterPayload):
    email = payload.email.lower()
    company_name = payload.company_name
    
    # 1. Send magic link email
    token = create_magic_link_token(email, company_name)
    login_url = f"{FRONTEND_URL}/org/verify?token={token}"
    
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                sender_address, sender_name = get_sender_for_send(cur)
    except Exception:
        sender_address = os.environ.get("ACS_SENDER_ADDRESS", "founders@orchvate.in")
        sender_name = os.environ.get("ACS_SENDER_NAME", "Orchvate")

    email_html = f"""
    <p>Hello,</p>
    <p>Please click the link below to access your NeuroMark Org Dashboard:</p>
    <p><a href="{login_url}" style="font-weight:bold;color:#7F77DD;">Access my Dashboard</a></p>
    <p>This link is valid for 15 minutes.</p>
    """
    
    try:
        send_acs_email(
            to_address=email,
            to_name=company_name,
            subject="Access your NeuroMark Org Dashboard",
            html=email_html,
            plain=f"Click here to log in: {login_url}",
            sender_address=sender_address,
            sender_name=sender_name
        )
    except Exception as e:
        logger.error(f"Failed to send magic link: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification email.")
        
    return {"success": True, "message": "Magic link sent to your email."}

@router.get("/verify")
async def verify_magic_link(token: str):
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("type") != "magic_link":
            raise HTTPException(status_code=400, detail="Invalid token type.")
        email = payload.get("email").lower()
        company_name = payload.get("company_name")
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Verification link has expired.")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid link token.")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    # Get or Create Organization
                    cur.execute("SELECT id FROM organizations WHERE name = %s", (company_name,))
                    org_row = cur.fetchone()
                    if org_row:
                        org_id = org_row[0]
                    else:
                        cur.execute("INSERT INTO organizations (name, is_active, is_deleted, approval_status) VALUES (%s, TRUE, FALSE, 'approved') RETURNING id", (company_name,))
                        org_id = cur.fetchone()[0]

                    # Get or Create Org User
                    cur.execute("SELECT id FROM organization_users WHERE email = %s", (email,))
                    user_row = cur.fetchone()
                    if not user_row:
                        cur.execute("INSERT INTO organization_users (organization_id, email) VALUES (%s, %s) RETURNING id", (org_id, email))
                        user_row = cur.fetchone()
                    
                    # Claim older submissions that matched this email but had no organization_id
                    cur.execute("""
                        UPDATE submissions 
                        SET organization_id = %s 
                        WHERE email = %s AND organization_id IS NULL
                    """, (org_id, email))
    except Exception as e:
        logger.error(f"Error in verification database steps: {e}")
        raise HTTPException(status_code=500, detail="Database registration failed.")

    # Create 30-day session token
    exp = datetime.now(timezone.utc) + timedelta(days=30)
    session_token = jwt.encode({
        "email": email,
        "org_id": str(org_id),
        "exp": exp,
        "role": "org_member"
    }, JWT_SECRET, algorithm="HS256")
    
    return {
        "success": True,
        "token": session_token,
        "organization": {"id": str(org_id), "name": company_name},
        "email": email
    }

async def get_current_org_user(request: Request) -> dict:
    auth_header = request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    token = auth_header.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        if payload.get("role") != "org_member":
            raise HTTPException(status_code=403, detail="Forbidden")
        return payload
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Session expired or invalid")

@router.get("/dashboard")
async def get_org_dashboard(current_user: dict = Depends(get_current_org_user)):
    org_id = current_user.get("org_id")
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, designation, company_name, email, submitted_at,
                           overall_avg, overall_level, status,
                           lc_score, ro_score, we_score, be_score,
                           tm_score, ca_score, pc_score, sp_score
                    FROM submissions
                    WHERE organization_id = %s
                    ORDER BY submitted_at ASC
                """, (org_id,))
                submissions = cur.fetchall()
    except Exception as e:
        logger.error(f"Dashboard query failed: {e}")
        raise HTTPException(status_code=500, detail="Database query failed.")

    history = []
    current_level = "Foundational"
    last_audit_date = None
    
    for sub in submissions:
        submitted_at_iso = to_iso_utc(sub["submitted_at"]) if sub.get("submitted_at") else None
        history.append({
            "date": submitted_at_iso,
            "score": float(sub["overall_avg"]) if sub.get("overall_avg") else 0.0
        })
        current_level = sub["overall_level"]
        last_audit_date = submitted_at_iso

    return {
        "submissions": [dict(s) for s in submissions],
        "history": history,
        "current_level": current_level,
        "last_audit_date": last_audit_date
    }

```

#### `app/api/orgs.py`

```python
"""
orgs.py — Admin endpoints for multi-respondent org scoring, organisation management, and invitation links.

All routes are under /manage/orgs and protected for Normal Admin and Super Admin.
"""

from collections import defaultdict
import hashlib
import logging
import secrets
from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

import psycopg2.extras
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from pydantic import BaseModel, Field

from app.core.database import get_db_connection
from app.core.authorization import require_admin
from app.services.org_scoring_service import calc_weighted_org_score, build_org_summary_email
from app.services.settings_service import send_acs_email, get_sender_for_send
from app.services.org_cache_service import invalidate_org_cache
from app.services.token_service import (
    create_assessment_token,
    revoke_assessment_token,
    get_or_create_default_token,
)

router = APIRouter(
    prefix="/manage/orgs",
    tags=["Org Scoring & Management"],
    dependencies=[Depends(require_admin)]
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Request Models
# ---------------------------------------------------------------------------

class CreateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class UpdateOrgRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class OrgStatusRequest(BaseModel):
    is_active: bool


class CreateInvitationRequest(BaseModel):
    invitation_name: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    max_submissions: Optional[int] = Field(None, ge=1)


class UpdateInvitationRequest(BaseModel):
    invitation_name: Optional[str] = Field(None, max_length=255)
    expires_at: Optional[datetime] = None
    max_submissions: Optional[int] = Field(None, ge=1)


class CreateAssessmentLinkRequest(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    campaign_id: Optional[UUID] = None
    expires_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _serialize_row(row: dict) -> dict:
    """Convert non-JSON-serialisable types in a DB row."""
    from decimal import Decimal
    from datetime import datetime
    import json
    out = {}
    for k, v in row.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat()
        elif isinstance(v, UUID):
            out[k] = str(v)
        else:
            out[k] = v
    if isinstance(out.get("answers"), str):
        try:
            out["answers"] = json.loads(out["answers"])
        except Exception:
            pass
    return out


def _fetch_org_links(conn, org_id: str) -> list[dict]:
    """Return all linked submissions for an org, enriched with weight and submission method."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("""
            SELECT
                s.*,
                osl.weight, osl.linked_by, osl.linked_at,
                s.submission_source,
                s.invitation_id,
                oi.invitation_name
            FROM org_submission_links osl
            JOIN submissions s ON s.id = osl.submission_id
            LEFT JOIN organization_invitations oi ON oi.id = s.invitation_id
            WHERE osl.org_id = %s
            ORDER BY s.submitted_at ASC
        """, (org_id,))
        return [_serialize_row(dict(r)) for r in cur.fetchall()]


# ---------------------------------------------------------------------------
# GET /api/manage/orgs
# List all orgs with weighted avg summary, active status, invitation counts,
# PLUS virtual groups for unlinked submissions.
# Optimized: Batch queries to eliminate N+1 loops.
# ---------------------------------------------------------------------------

@router.get("")
def list_orgs(include_deleted: bool = Query(False)):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. Real org accounts
                where_clause = "" if include_deleted else "WHERE o.is_deleted = FALSE"
                cur.execute(f"""
                    SELECT o.id, o.name, o.is_active, o.is_deleted, o.created_at, o.updated_at,
                           (
                               COUNT(DISTINCT osl.submission_id) +
                               COALESCE((
                                   SELECT COUNT(*) FROM raw_submissions r 
                                   WHERE (r.organization_id = o.id OR LOWER(TRIM(r.payload->>'company_name')) = LOWER(TRIM(o.name)))
                                     AND r.status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING')
                                     AND NOT EXISTS (
                                         SELECT 1 FROM submissions s WHERE s.id = r.submission_id OR s.raw_submission_id = r.submission_id
                                     )
                               ), 0)
                           ) AS respondent_count,
                           COUNT(DISTINCT oi.id) FILTER (
                               WHERE oi.is_active = TRUE AND (oi.expires_at IS NULL OR oi.expires_at > NOW())
                           ) AS active_invitations_count
                    FROM organizations o
                    LEFT JOIN org_submission_links osl ON osl.org_id = o.id
                    LEFT JOIN organization_invitations oi ON oi.organization_id = o.id
                    {where_clause}
                    GROUP BY o.id, o.name, o.is_active, o.is_deleted, o.created_at, o.updated_at
                    ORDER BY o.name ASC
                """)
                orgs = [_serialize_row(dict(r)) for r in cur.fetchall()]

                # 2. Batch fetch all linked submissions to eliminate N+1 query loop
                cur.execute("""
                    SELECT
                        s.*,
                        osl.org_id,
                        osl.weight, osl.linked_by, osl.linked_at,
                        s.submission_source,
                        s.invitation_id,
                        oi.invitation_name
                    FROM org_submission_links osl
                    JOIN submissions s ON s.id = osl.submission_id
                    LEFT JOIN organization_invitations oi ON oi.id = s.invitation_id
                    ORDER BY s.submitted_at ASC
                """)
                all_links = cur.fetchall()
                links_by_org = defaultdict(list)
                for r in all_links:
                    d = _serialize_row(dict(r))
                    links_by_org[str(d["org_id"])].append(d)

                # 3. Unlinked submissions grouped by company_name (virtual groups)
                cur.execute("""
                    SELECT
                        LOWER(TRIM(s.company_name)) AS name_key,
                        MIN(s.company_name)          AS display_name,
                        COUNT(*)                     AS respondent_count,
                        AVG(s.overall_avg)           AS org_avg
                    FROM submissions s
                    WHERE NOT EXISTS (
                        SELECT 1 FROM org_submission_links osl
                        WHERE osl.submission_id = s.id
                    )
                    GROUP BY LOWER(TRIM(s.company_name))
                    ORDER BY display_name ASC
                """)
                unlinked_groups = cur.fetchall()

            # Compute weighted avg for real orgs from batched links
            result = []
            for org in orgs:
                org_links = links_by_org.get(str(org["id"]), [])
                scores = calc_weighted_org_score(org_links) if org_links else None
                result.append({
                    **org,
                    "org_avg":                  scores["org_avg"]   if scores else None,
                    "org_level":                scores["org_level"] if scores else None,
                    "is_virtual":               False,
                    "active_invitations_count": int(org.get("active_invitations_count") or 0),
                })

            # Add virtual groups (unlinked, grouped by company_name)
            for g in unlinked_groups:
                name_key = g["name_key"] or ""
                real_names = {o["name"].lower().strip() for o in orgs}
                if name_key in real_names:
                    continue
                fake_id = "virtual-" + hashlib.md5(name_key.encode()).hexdigest()[:12]
                avg = float(g["org_avg"]) if g["org_avg"] else None
                result.append({
                    "id":                       fake_id,
                    "name":                     g["display_name"],
                    "is_active":                True,
                    "is_deleted":               False,
                    "created_at":               None,
                    "updated_at":               None,
                    "respondent_count":         int(g["respondent_count"]),
                    "active_invitations_count": 0,
                    "org_avg":                  round(avg, 2) if avg else None,
                    "org_level":                None,
                    "is_virtual":               True,
                })

        return result
    except Exception as e:
        logger.error("list_orgs failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# POST /api/manage/orgs
# Create a new formal organisation
# ---------------------------------------------------------------------------

@router.post("")
async def create_org(request: Request, body: CreateOrgRequest):
    company_name = " ".join(body.name.strip().split())
    if not company_name:
        raise HTTPException(status_code=400, detail="Organization name is required")

    admin_email = getattr(request.state, "admin_email", "unknown")

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # Check for existing non-deleted org (case and whitespace normalized)
                    cur.execute("""
                        SELECT id FROM organizations
                        WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) AND is_deleted = FALSE
                    """, (company_name,))
                    if cur.fetchone():
                        raise HTTPException(status_code=400, detail="An organization with this name already exists")

                    cur.execute("""
                        INSERT INTO organizations (name, is_active, is_deleted, approval_status, updated_by)
                        VALUES (%s, TRUE, FALSE, 'approved', %s)
                        RETURNING id, name, is_active, is_deleted, created_at
                    """, (company_name, admin_email))
                    row = cur.fetchone()
                    org_id = str(row["id"])

                    # Link all unlinked submissions matching this company_name
                    cur.execute("""
                        SELECT id FROM submissions s
                        WHERE LOWER(TRIM(s.company_name)) = LOWER(TRIM(%s))
                        AND NOT EXISTS (
                            SELECT 1 FROM org_submission_links osl WHERE osl.submission_id = s.id
                        )
                    """, (company_name,))
                    sub_ids = [str(r["id"]) for r in cur.fetchall()]

                    for sid in sub_ids:
                        cur.execute("""
                            INSERT INTO org_submission_links (org_id, submission_id, weight, linked_by)
                            VALUES (%s, %s, 1.0, %s)
                            ON CONFLICT (org_id, submission_id) DO NOTHING
                        """, (org_id, sid, admin_email))
                        cur.execute("""
                            UPDATE submissions SET organization_id = %s
                            WHERE id = %s AND organization_id IS NULL
                        """, (org_id, sid))

        try:
            invalidate_org_cache()
        except Exception as err:
            logger.warning("Cache invalidation failed on create_org: %s", err)

        return {
            "success": True,
            "org": _serialize_row(dict(row)),
            "linked_count": len(sub_ids)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_org failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# Legacy alias: POST /api/manage/orgs/create
@router.post("/create")
async def create_org_legacy(request: Request):
    try:
        body = await request.json()
        name = (body.get("company_name") or body.get("name") or "").strip()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")
    return await create_org(request, CreateOrgRequest(name=name))


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/unlinked
# Submissions with no org link — optionally filtered by company_name
# ---------------------------------------------------------------------------

@router.get("/unlinked")
async def list_unlinked(company_name: str = None):
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                if company_name:
                    cur.execute("""
                        SELECT s.*
                        FROM submissions s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM org_submission_links osl
                            WHERE osl.submission_id = s.id
                        )
                        AND LOWER(TRIM(s.company_name)) = LOWER(TRIM(%s))
                        ORDER BY s.submitted_at DESC
                    """, (company_name,))
                else:
                    cur.execute("""
                        SELECT s.*
                        FROM submissions s
                        WHERE NOT EXISTS (
                            SELECT 1 FROM org_submission_links osl
                            WHERE osl.submission_id = s.id
                        )
                        ORDER BY s.submitted_at DESC
                    """)
                rows = [_serialize_row(dict(r)) for r in cur.fetchall()]
        return rows
    except Exception as e:
        logger.error("list_unlinked failed: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


# ---------------------------------------------------------------------------
# GET /api/manage/orgs/{org_id}
# Org detail with all linked submissions + live weighted scores
# ---------------------------------------------------------------------------

@router.get("/{org_id}")
async def get_org(org_id: UUID):
    oid = str(org_id)
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, created_at, updated_at
                    FROM organizations
                    WHERE id = %s
       
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `app/api/public.py`

```python
"""
public.py — Public endpoints for NIWI Assessment Dual Entry.
- POST /api/public/organisations/validate: Validate organisation name for direct assessment
- POST /api/public/invitations/validate: Validate invitation token for invitation-based assessment
"""

import os
import hashlib
import logging
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Request, Body
from pydantic import BaseModel, Field
import psycopg2.extras

from app.core.database import get_db_connection
from app.core.limiter import limiter
from app.services.org_cache_service import get_organisation_by_name, is_org_eligible
from app.services.email_policy_service import check_corporate_email_eligibility
from app.services.token_service import resolve_assessment_token, get_or_create_default_token

router = APIRouter(prefix="/public", tags=["Public Assessment"])
logger = logging.getLogger(__name__)


class ValidateInvitationRequest(BaseModel):
    token: str = Field(..., min_length=1)


class ValidateOrganisationRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)


class ValidateEmailRequest(BaseModel):
    email: str = Field(..., min_length=3, max_length=254)


class ResolveLinkRequest(BaseModel):
    token: str = Field(..., min_length=1, max_length=512)


class ResolveLegacyOrgRequest(BaseModel):
    org: str = Field(..., min_length=1, max_length=255)


@router.post("/assessment/resolve-link")
@limiter.limit("120/minute")
async def resolve_assessment_link_endpoint(request: Request, body: ResolveLinkRequest):
    """
    Resolves a secure assessment token to its organisation and campaign context.
    Eliminates exposure of organisation names and codes in URLs.
    """
    raw_token = body.token.strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Token is required")
    
    try:
        result = resolve_assessment_token(raw_token)
        return result
    except Exception as e:
        logger.error("resolve_assessment_link failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve assessment link")


@router.post("/assessment/resolve-legacy-org")
@limiter.limit("120/minute")
async def resolve_legacy_org(request: Request, body: ResolveLegacyOrgRequest):
    """
    Backward compatibility endpoint for legacy links (?org=SKY11).
    Resolves the organisation securely from cache, ensures a secure opaque token exists,
    and returns the secure token and masked assessment URL so the frontend can
    instantly replace the URL in the address bar without exposing the organisation name.
    """
    org_name = body.org.strip()
    if not org_name:
        raise HTTPException(status_code=400, detail="Organisation name is required")

    org, _ = get_organisation_by_name(org_name)
    if not org:
        raise HTTPException(status_code=404, detail="Organisation not found")

    eligible, err = is_org_eligible(org)
    if not eligible:
        raise HTTPException(status_code=400, detail=err or "Organisation is inactive")

    try:
        token_info = get_or_create_default_token(org["id"])
        return {
            "valid": True,
            "token": token_info["raw_token"],
            "organization_id": str(org["id"]),
            "organization_name": org["name"],
            "assessment_url": f"/audit?t={token_info['raw_token']}",
        }
    except Exception as e:
        logger.error("resolve_legacy_org failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to resolve organisation link")


@router.post("/email/validate")
@limiter.limit("120/minute")
async def validate_corporate_email(request: Request, body: ValidateEmailRequest):
    """
    Checks corporate email eligibility without requiring OTP or mailbox authentication.
    Accepts any corporate domain and rejects known personal/free email providers.
    """
    return check_corporate_email_eligibility(body.email)


@router.post("/organisations/validate")
@limiter.limit(lambda: os.environ.get("PUBLIC_VALIDATE_LIMIT", "2000/minute"))
async def validate_organisation_by_name(request: Request, body: ValidateOrganisationRequest):
    """
    Validates a manually entered organisation name against existing records.
    Returns minimal information without exposing organisation directory.
    Uses high-performance in-memory organisation registry cache with sub-10ms latency.
    """
    name = body.name.strip()
    if not name:
        return {
            "valid": False,
            "error": "Organisation name cannot be empty"
        }
    
    try:
        org, source = get_organisation_by_name(name)
        if not org:
            return {
                "valid": False,
                "error": "We couldn't find this organisation. Please check the spelling or contact your administrator."
            }
        
        eligible, err = is_org_eligible(org)
        if not eligible:
            return {
                "valid": False,
                "error": err
            }
        
        return {
            "valid": True,
            "organization_id": str(org["id"]),
            "organization_name": org["name"]  # Return canonical spelling
        }
    except Exception as e:
        logger.error("validate_organisation_by_name failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to validate organisation")


@router.post("/invitations/validate")
@limiter.limit("30/minute")
async def validate_invitation(request: Request, body: ValidateInvitationRequest):
    """
    Validates an invitation token without leaking sensitive org internals.
    Derives whether the token is valid, active, non-expired, and within limits.
    """
    raw_token = body.token.strip()
    if not raw_token:
        raise HTTPException(status_code=400, detail="Token is required")

    token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT 
                        oi.id AS invitation_id,
                        oi.organization_id,
                        oi.invitation_name,
                        oi.expires_at,
                        oi.is_active AS invitation_active,
                        oi.max_submissions,
                        oi.submission_count,
                        oi.revoked_at,
                        o.name AS organization_name,
                        o.is_active AS org_active,
                        o.is_deleted AS org_deleted
                    FROM organization_invitations oi
                    JOIN organizations o ON o.id = oi.organization_id
                    WHERE oi.token_hash = %s
                """, (token_hash,))
                inv = cur.fetchone()

        if not inv:
            return {
                "valid": False,
                "error": "This invitation link is invalid or does not exist."
            }

        # Check organization status
        if inv["org_deleted"] or not inv["org_active"]:
            return {
                "valid": False,
                "error": "The organization associated with this invitation is inactive."
            }

        # Check invitation status
        if not inv["invitation_active"] or inv["revoked_at"] is not None:
            return {
                "valid": False,
                "error": "This invitation link has been revoked or deactivated."
            }

        # Check expiration
        now = datetime.now(timezone.utc)
        if inv["expires_at"] and inv["expires_at"] < now:
            return {
                "valid": False,
                "error": "This invitation link has expired."
            }

        # Check maximum submissions limit
        if inv["max_submissions"] is not None and inv["submission_count"] >= inv["max_submissions"]:
            return {
                "valid": False,
                "error": "This invitation link has reached its maximum allowed submissions."
            }

        return {
            "valid": True,
            "organization_name": inv["organization_name"],
            "invitation_name": inv["invitation_name"] or "Assessment Invitation",
            "expires_at": inv["expires_at"].isoformat() if inv["expires_at"] else None,
            "submission_count": inv["submission_count"],
            "max_submissions": inv["max_submissions"],
        }
    except Exception as e:
        logger.error("validate_invitation failed: %s", e)
        raise HTTPException(status_code=500, detail="Failed to validate invitation")

```

#### `app/api/routes.py`

```python
"""
routes.py — FastAPI route definitions
Ported from Azure Functions (function_app.py).
All routes are prefixed with /api via the router prefix in main.py.
"""

import hashlib
import json
import logging
import math
import os
import re
import threading
import time
from datetime import datetime, timezone, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID
import uuid as uuid_pkg

from cachetools import TTLCache
from fastapi import APIRouter, HTTPException, Request, Response, BackgroundTasks, Depends, status, Query
from fastapi.responses import JSONResponse
import jwt
import psycopg2
import psycopg2.extras

from app.api.drafts import router as drafts_router
from app.api.org import router as org_router
from app.api.orgs import router as orgs_router
from app.api.public import router as public_router
from app.core.authorization import (
    get_user_from_request,
    filter_submissions_by_org_access,
    check_submission_access,
    get_admin_organizations,
    require_admin,
    require_super_admin,
)
from app.core.config import JWT_SECRET
from app.core.database import get_conn, get_db_connection, get_db_transaction
from app.core.limiter import limiter
from app.core.security import audit_log
from app.models.audit import AuditSubmission
from app.services.crm_service import sync_to_hubspot
from app.services.filter_service import (
    build_filter_query,
    ALLOWED_FILTER_FIELDS,
    ALLOWED_SORT_FIELDS,
)
from app.services.scoring_service import calculate_scores, calculate_scores_pure, get_form_sections_metadata, build_email
from app.services.settings_service import (
    get_settings,
    get_sender_for_send,
    notify_admin_new_submission,
    send_acs_email,
    send_support_request,
    update_settings,
)
from app.services.user_service import add_user, get_users, remove_user, verify_user
from app.utils.helpers import to_iso_utc
from app.services.org_cache_service import (
    get_organisation_by_name,
    get_organisation_by_id,
    is_org_eligible,
    invalidate_org_cache,
)
from app.services.email_policy_service import check_corporate_email_eligibility
from app.services.token_service import resolve_assessment_token
from app.services.rate_limit_service import (
    enforce_submission_rate_limits,
    get_effective_submit_hourly_limit,
    get_effective_submit_daily_limit,
    get_client_ip,
    get_rate_limit_config_response,
    update_rate_limit_settings,
    reset_rate_limit_settings,
)

logger = logging.getLogger(__name__)

router = APIRouter()
router.include_router(drafts_router)
router.include_router(org_router)
router.include_router(orgs_router)
router.include_router(public_router)

# Organization-aware dashboard cache: keys are (admin_email, org_filter_hash)
# TTL of 60 seconds to balance performance and data freshness
dashboard_cache = TTLCache(maxsize=500, ttl=60)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def serialize(obj: Any) -> Any:
    if isinstance(obj, Decimal):
        return float(obj)
    if isinstance(obj, datetime):
        return to_iso_utc(obj)
    if isinstance(obj, UUID):
        return str(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def strip_html(html: str) -> str:
    text = re.sub(r"<br\s*/?>", "\n", html)
    text = re.sub(r"</p>", "\n", text)
    text = re.sub(r"</li>", "\n", text)
    text = re.sub(r"<[^>]+>", "", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _bg_notify_admin(submission_id: str, name: str, company_name: str):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                notify_admin_new_submission(cur, submission_id, name, company_name)
    except Exception as e:
        logger.error(f"Failed to send admin notification for submission {submission_id}: {e}")


# ---------------------------------------------------------------------------
# POST /api/submit
# ---------------------------------------------------------------------------

@router.post("/submit", status_code=status.HTTP_202_ACCEPTED)
@limiter.limit(get_effective_submit_hourly_limit, key_func=get_client_ip)
@limiter.limit(get_effective_submit_daily_limit, key_func=get_client_ip)
def submit(request: Request, payload: AuditSubmission, response: Response, background_tasks: BackgroundTasks):
    t_req_start = time.perf_counter()
    data = payload.dict()
    idempotency_key = (data.get("idempotency_key") or request.headers.get("Idempotency-Key") or "").strip()
    if not idempotency_key:
        idempotency_key = str(uuid_pkg.uuid4())

    # Step 0: Dynamic per-traffic classification and session attempt rate limiting
    enforce_submission_rate_limits(request, data)

    # Step 1: Validate Corporate Email Eligibility
    user_email = (data.get("email") or "").strip()
    if user_email:
        email_check = check_corporate_email_eligibility(user_email)
        if not email_check["eligible"]:
            raise HTTPException(status_code=400, detail=email_check.get("error", "Corporate email is required."))

    # Step 2: Organization / Token / Invitation resolution
    organization_id = None
    invitation_id = None
    access_token_id = None
    campaign_id = None
    submission_source = "DIRECT"
    resolved_company_name = (data.get("company_name") or "").strip()

    raw_token = (data.get("t") or data.get("token") or data.get("access_token") or data.get("invitation_token") or "").strip()
    if raw_token:
        token_res = resolve_assessment_token(raw_token)
        if not token_res.get("valid"):
            raise HTTPException(status_code=400, detail=token_res.get("error", "Invalid assessment link."))

        organization_id = str(token_res["organization_id"])
        resolved_company_name = token_res["organization_name"]
        campaign_id = token_res.get("campaign_id")
        if token_res.get("is_legacy_invitation"):
            invitation_id = str(token_res["token_id"])
            submission_source = "INVITATION"
        else:
            access_token_id = str(token_res["token_id"])
            submission_source = "SECURE_LINK"
    else:
        req_org_id = data.get("organization_id")
        auth_header = request.headers.get("Authorization")
        if not req_org_id and auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
            try:
                token_payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
                if token_payload.get("role") == "org_member":
                    req_org_id = token_payload.get("org_id")
            except Exception:
                pass

        if req_org_id:
            org, _ = get_organisation_by_id(req_org_id)
            if not org:
                raise HTTPException(status_code=400, detail="Invalid organisation ID.")
            eligible, err = is_org_eligible(org)
            if not eligible:
                raise HTTPException(status_code=400, detail=err or "Organisation is inactive.")
            organization_id = str(org["id"])
            resolved_company_name = org["name"]
            submission_source = "DIRECT"
        elif resolved_company_name:
            clean_name = " ".join(resolved_company_name.split())
            org, _ = get_organisation_by_name(clean_name)
            if org:
                eligible, err = is_org_eligible(org)
                if not eligible:
                    raise HTTPException(status_code=400, detail=err or "Organisation is inactive.")
                organization_id = str(org["id"])
                resolved_company_name = org["name"]
            else:
                with get_db_connection() as org_conn:
                    with org_conn:
                        with org_conn.cursor() as org_cur:
                            org_cur.execute(
                                "SELECT pg_advisory_xact_lock(hashtext(lower(trim(%s))))",
                                (clean_name,)
                            )
                            org_cur.execute("""
                                SELECT id, name FROM organizations 
                                WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s)) AND is_deleted = FALSE
                            """, (clean_name,))
                            org_row = org_cur.fetchone()
                            if org_row:
                                organization_id = str(org_row[0])
                                resolved_company_name = org_row[1]
                            else:
                                org_cur.execute("""
                                    INSERT INTO organizations (name, is_active, is_deleted, approval_status)
                                    VALUES (%s, TRUE, FALSE, 'approved')
                                    RETURNING id, name
                                """, (clean_name,))
                                new_org = org_cur.fetchone()
                                organization_id = str(new_org[0])
                                resolved_company_name = new_org[1]
                                try:
                                    invalidate_org_cache()
                                except Exception:
                                    pass
            submission_source = "DIRECT"
        else:
            raise HTTPException(status_code=400, detail="Organisation name or ID is required.")

    # Attach resolved properties for the background worker
    data["_resolved_org_id"] = organization_id
    data["_resolved_company_name"] = resolved_company_name
    data["_resolved_source"] = submission_source
    data["_invitation_id"] = invitation_id
    data["_access_token_id"] = access_token_id
    data["_campaign_id"] = campaign_id

    draft_uuid = None
    draft_id = data.get("draft_id")
    if draft_id and str(draft_id).strip() not in ("", "null", "undefined"):
        try:
            draft_uuid = str(uuid_pkg.UUID(str(draft_id)))
        except ValueError:
            logger.warning("Invalid draft_id UUID: %s", draft_id)

    new_sub_id = str(uuid_pkg.uuid4())

    # Step 3: Single atomic transaction - write raw submission & outbox
    cte_sql = """
        WITH existing_raw AS (
            SELECT submission_id, payload, status FROM raw_submissions
            WHERE idempotency_key = %(idempotency_key)s
            LIMIT 1
        ),
        new_raw AS (
            INSERT INTO raw_submissions (
                submission_id, idempotency_key, organization_id, user_id,
                payload, schema_version, status, scoring_status, report_status,
                email_status, crm_status
            )
            SELECT
                %(submission_id)s::uuid,
                %(idempotency_key)s,
                %(organization_id)s::uuid,
                %(user_id)s,
                %(payload)s::jsonb,
                1,
                'RECEIVED',
                'PENDING',
                'PENDING',
                'PENDING',
                'PENDING'
            WHERE NOT EXISTS (SELECT 1 FROM existing_raw)
            ON CONFLICT (idempotency_key) DO NOTHING
            RETURNING submission_id
        ),
        new_outbox AS (
            INSERT INTO service_bus_outbox (
                event_type, aggregate_id, message_id, payload, status
            )
            SELECT
                'SUBMISSION_CREATED',
                submission_id,
                submission_id::text,
                json_build_object(
                    'submission_id', submission_id::text,
                    'organization_id', %(organization_id)s::text,
                    'idempotency_key', %(idempotency_key)s
                )::jsonb,
                'PENDING'
            FROM new_raw
        ),
        update_invitation AS (
            UPDATE organization_invitations
            SET submission_count = submission_count + 1
            WHERE %(invitation_id)s IS NOT NULL AND id = %(invitation_id)s::uuid
              AND EXISTS (SELECT 1 FROM new_raw)
        ),
        update_draft AS (
            UPDATE draft_submissions
            SET submitted = TRUE
            WHERE %(draft_uuid)s IS NOT NULL AND id = %(draft_uuid)s::uuid
              AND EXISTS (SELECT 1 FROM new_raw)
        )
        SELECT 
            (SELECT submission_id FROM new_raw) AS created_id,
            (SELECT submission_id FROM existing_raw) AS existing_id,
            (SELECT status FROM existing_raw) AS existing_status,
            (SELECT payload FROM existing_raw) AS existing_payload;
    """

    params = {
        "submission_id": new_sub_id,
        "idempotency_key": idempotency_key,
        "organization_id": organization_id,
        "user_id": data.get("user_id") or data.get("email"),
        "payload": json.dumps(data),
        "invitation_id": invitation_id,
        "draft_uuid": draft_uuid
    }

    t_checkout_start = time.perf_counter()
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(cte_sql, params)
                res = cur.fetchone()

    t_tx_end = time.perf_counter()
    created_id, existing_id, existing_status, existing_payload = res

    if existing_id:
        if existing_payload and isinstance(existing_payload, dict):
            existing_email = (existing_payload.get("email") or "").strip().lower()
            incoming_email = (data.get("email") or "").strip().lower()
            if existing_email and incoming_email and existing_email != incoming_email:
                logger.warning("Idempotency key %s reused with conflicting email: %s vs %s",
                               idempotency_key, incoming_email, existing_email)
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail="Idempotency key has already been used with a different payload."
                )
        logger.info("Idempotent replay detected for key %s, returning submission %s (status=%s)",
                    idempotency_key, existing_id, existing_status)
        response.status_code = status.HTTP_200_OK if existing_status == "COMPLETED" else status.HTTP_202_ACCEPTED
        return {
            "success": True,
            "submission_id": str(existing_id),
            "status": existing_status or "RECEIVED",
            "message": "Your submission has been received and is being processed."
        }

    if not created_id:
        # Fallback query for millisecond concurrency collision
        with get_db_connection() as fb_conn:
            with fb_conn.cursor() as fb_cur:
                fb_cur.execute(
                    "SELECT submission_id, status FROM raw_submissions WHERE idempotency_key = %s LIMIT 1",
                    (idempotency_key,)
                )
                fb_row = fb_cur.fetchone()
                if fb_row:
                    logger.info("Recovered parallel idempotency conflict for key %s -> %s", idempotency_key, fb_row[0])
                    response.status_code = status.HTTP_202_ACCEPTED
                    return {
                        "success": True,
                        "submission_id": str(fb_row[0]),
                        "status": fb_row[1] or "RECEIVED",
                        "message": "Your submission has been received and is being processed."
                    }

        logger.error("Failed to persist raw submission for key %s", idempotency_key)
        raise HTTPException(status_code=500, detail="Database error persisting submission")

    submission_id = str(created_id)

    t_req_end = time.perf_counter()
    logger.info(
        "INGESTION_METRICS: id=%s total_ms=%.2f tx_ms=%.2f",
        submission_id,
        (t_req_end - t_req_start) * 1000.0,
        (t_tx_end - t_checkout_start) * 1000.0
    )

    response.status_code = status.HTTP_202_ACCEPTED
    return {
        "success": True,
        "submission_id": submission_id,
       
```
> _Truncated to 16000 bytes — see full file in the source repo._


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

