# Business Logic & Core Scoring Services

> Unit `07-services` · kind: feature

## Summary

Deterministic 0–160 inclusion scoring algorithm, 8-pillar calculations, maturity tier resolution, and outbox orchestration.

## Context & goal

The Services unit represents the core business logic domain of NIWI. It calculates pillar scores (0–20 points per dimension) and aggregate scores (0–160 total), maps totals to 5 maturity tiers, coordinates transactional outbox staging, manages in-memory organization caches, and executes email delivery workflows.

## User stories

- As an Audit Respondent, my assessment responses are scored deterministically across all 8 dimensions according to Orchvate methodology.
- As an HR Leader, I receive an objective maturity tier categorization with targeted recommendations.
- As a System Architect, I rely on the transactional outbox service to ensure guaranteed at-least-once message delivery without distributed 2PC.

## Functional requirements

- 1. 8-Pillar Score Calculation [confirmed]: Calculate scores across Physical Environment, Hiring, Culture, Policies, Career, Communication, Daily Operations, and Wellbeing (5 questions per pillar, normalized to 0–20 points).
- 2. Maturity Tier Mapping [confirmed]: Map total score (0–160) to Foundational (0–39), Early Progress (40–79), Developing (80–119), Proficient (120–139), or Leading (140–160).
- 3. Transactional Outbox Staging [confirmed]: Atomically write incoming survey payloads into `raw_submissions` and `service_bus_outbox`.
- 4. Organization Score Aggregation [confirmed]: Calculate cross-employee average inclusion scores, response counts, and departmental radar data.
- 5. Dual-Layer Caching [confirmed]: Maintain in-memory caches for organization lookups and section metadata with periodic invalidation.


## Interfaces & data

Invoked by route handlers in `app/api/` and background tasks in `app/tasks/`.
Reads and writes to `submissions`, `raw_submissions`, `service_bus_outbox`, and `organizations` (see [DATA-MODEL.md](../../architecture/DATA-MODEL.md)).

## Acceptance criteria

- Given 40 Likert answers all answered with '5' (Strongly Agree), When scored, Then total score equals 160 and maturity tier equals 'Leading'.
- Given 40 Likert answers all answered with '1' (Strongly Disagree), When scored, Then total score equals 0 and maturity tier equals 'Foundational'.
- Given an outbox message, When processed successfully, Then status is updated to 'completed' and `processed_at` timestamp is set.

## Edge cases & failure modes

- **Incomplete pillar responses:** Scoring service raises ValueError if any pillar contains fewer than the required question inputs.
- **Concurrent cache invalidation:** Thread-safe locks prevent race conditions during organization cache reloads.

## Definition of done

- All functional requirements implemented and verified against code.
- All acceptance scenarios verified with passing unit or integration tests.
- Zero unresolved callouts, placeholders, or ambiguous specifications.
- Security and authorization policies strictly enforced.
- Performance and error recovery verified under edge conditions.

## Improvements & enhancements

- Incorporate Azure OpenAI (`gpt-4o-mini`) integration for dynamic executive summary narrative generation.
- Support configurable pillar weighting schemes for customized enterprise audits.


## Source material

Key source for this unit (16 file(s) total, showing up to 15):

#### `app/services/__init__.py`

```python

```

#### `app/services/ai_service.py`

```python
"""
ai_service.py — AI-assisted features (future use)
Placeholder for any LLM-based interpretation or recommendation generation.
"""

```

#### `app/services/audit_service.py`

```python
"""
audit_service.py — CRUD operations for audit submissions
"""
import psycopg2.extras
from app.core.database import get_conn


def get_all_submissions():
    conn = get_conn()
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("""
                SELECT id, name, company_name, email, submitted_at,
                       overall_avg, overall_level, status
                FROM submissions ORDER BY submitted_at DESC
            """)
            return [dict(r) for r in cur.fetchall()]


def get_submission(submission_id: int):
    conn = get_conn()
    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM submissions WHERE id = %s", (submission_id,))
            row = cur.fetchone()
            return dict(row) if row else None


def update_email_body(submission_id: int, email_body: str):
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE submissions SET email_body = %s WHERE id = %s",
                (email_body, submission_id),
            )
            return cur.rowcount > 0


def mark_sent(submission_id: int, sent_at):
    conn = get_conn()
    with conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE submissions SET status = 'sent', sent_at = %s WHERE id = %s",
                (sent_at, submission_id),
            )

```

#### `app/services/crm_service.py`

```python
import os
import time
import logging
from datetime import datetime, timezone
import requests
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

HUBSPOT_ACCESS_TOKEN = os.environ.get("HUBSPOT_ACCESS_TOKEN", "")


def get_hubspot_token() -> str:
    """Retrieve HubSpot access token from module attribute, environment, or config."""
    global HUBSPOT_ACCESS_TOKEN
    return (HUBSPOT_ACCESS_TOKEN or os.environ.get("HUBSPOT_ACCESS_TOKEN", "")).strip()


def is_hubspot_configured() -> bool:
    """Check if HubSpot CRM integration is configured."""
    return bool(get_hubspot_token())


def make_hubspot_request(method: str, url: str, json_data: Any = None, retries: int = 3, timeout: int = 10) -> Dict[str, Any]:
    token = get_hubspot_token()
    if not token:
        logger.warning("HubSpot token missing. CRM request bypassed.")
        return {}

    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    delay = 1
    for attempt in range(retries):
        try:
            response = requests.request(method, url, headers=headers, json=json_data, timeout=timeout)
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", delay))
                logger.warning(f"HubSpot rate limit hit. Waiting {retry_after}s to retry...")
                time.sleep(retry_after)
                continue

            if response.status_code in (200, 201, 204):
                return response.json() if response.content else {}

            logger.error(f"HubSpot API returned status {response.status_code}: {response.text}")
            response.raise_for_status()
        except requests.exceptions.Timeout as te:
            logger.warning(
                "HubSpot API request timed out (attempt %d/%d) for %s %s. Operation may have been received remotely.",
                attempt + 1, retries, method, url
            )
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise te
        except Exception as e:
            logger.error(f"HubSpot request error (attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                time.sleep(delay)
                delay *= 2
            else:
                raise e
    return {}


def sync_to_hubspot(
    data: Dict[str, Any],
    score_data: Dict[str, Any],
    submission_id: str,
    known_deal_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Syncs the audit submission to HubSpot with deal idempotency.
    
    1. Checks if HubSpot integration is configured. If not, returns SKIPPED.
    2. Searches/creates/updates Contact by email.
    3. Searches for existing Deal using stable submission ID identifier.
    4. Updates existing deal if found, otherwise creates new deal.
    5. Associates deal with contact.
    6. Returns status dict with deal_id and contact_id.
    """
    if not is_hubspot_configured():
        logger.info("HubSpot access token not configured, skipping CRM sync for submission %s", submission_id)
        return {
            "status": "SKIPPED",
            "reason": "HUBSPOT_ACCESS_TOKEN not configured"
        }

    email = data.get("email")
    name = data.get("name") or ""
    company_name = data.get("company_name") or ""
    designation = data.get("designation") or ""
    contact_number = data.get("contact_number") or ""

    overall_avg = score_data.get("overall_avg", 0.0)
    overall_level = score_data.get("overall_level", "Foundational")

    # Map score to deal stages
    if overall_avg <= 6:
        deal_stage = "prospect"
    elif overall_avg <= 11:
        deal_stage = "qualifiedlead"
    elif overall_avg <= 15:
        deal_stage = "opportunity"
    else:
        deal_stage = "closedwon"

    # 1. Search if contact already exists
    search_url = "https://api.hubapi.com/crm/v3/objects/contacts/search"
    search_query = {
        "filterGroups": [{
            "filters": [{
                "propertyName": "email",
                "operator": "EQ",
                "value": email
            }]
        }]
    }

    contact_id = None
    try:
        search_res = make_hubspot_request("POST", search_url, search_query)
        if search_res.get("results"):
            contact_id = search_res["results"][0]["id"]
    except Exception as e:
        logger.warning(f"Could not query contact search (will attempt creation): {e}")

    properties = {
        "email": email,
        "firstname": name.split(" ")[0] if " " in name else name,
        "lastname": name.split(" ")[1] if " " in name else "",
        "company": company_name,
        "jobtitle": designation,
        "phone": contact_number,
        "maturity_score": str(overall_avg),
        "maturity_level": overall_level,
        "audit_id": submission_id
    }

    # 2. Create or Update Contact
    if contact_id:
        contact_url = f"https://api.hubapi.com/crm/v3/objects/contacts/{contact_id}"
        try:
            make_hubspot_request("PATCH", contact_url, {"properties": properties})
        except Exception as e:
            logger.error(f"Contact update failed: {e}")
            raise RuntimeError(f"HubSpot contact update failed: {e}") from e
    else:
        contact_url = "https://api.hubapi.com/crm/v3/objects/contacts"
        try:
            contact_res = make_hubspot_request("POST", contact_url, {"properties": properties})
            contact_id = contact_res.get("id")
            if not contact_id:
                raise RuntimeError("HubSpot contact creation succeeded without returning an id")
        except Exception as e:
            logger.error(f"Contact creation failed: {e}")
            raise RuntimeError(f"HubSpot contact creation failed: {e}") from e

    # 3. Idempotent Deal Management
    # Use stable submission ID in dealname and description for business identification
    stable_deal_name = f"NeuroMark Audit Deal — {company_name} [{submission_id}]"
    deal_properties = {
        "dealname": stable_deal_name,
        "dealstage": deal_stage,
        "pipeline": "default",
        "amount": "0",
        "description": f"NIWI Submission ID: {submission_id}",
        "maturity_score": str(overall_avg),
        "maturity_level": overall_level,
        "submission_date": datetime.now(timezone.utc).date().isoformat()
    }

    deal_id = known_deal_id

    # If deal ID not already known, search for an existing deal by dealname
    if not deal_id:
        deal_search_url = "https://api.hubapi.com/crm/v3/objects/deals/search"
        deal_search_query = {
            "filterGroups": [{
                "filters": [{
                    "propertyName": "dealname",
                    "operator": "EQ",
                    "value": stable_deal_name
                }]
            }],
            "properties": ["dealname", "dealstage", "pipeline", "amount"]
        }
        try:
            deal_search_res = make_hubspot_request("POST", deal_search_url, deal_search_query)
            if deal_search_res.get("results"):
                deal_id = deal_search_res["results"][0]["id"]
                logger.info("Found existing HubSpot deal %s for submission %s, updating deal", deal_id, submission_id)
        except Exception as e:
            logger.warning("Could not query deal search for submission %s: %s", submission_id, e)

    # Update existing deal or create new one
    if deal_id:
        update_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}"
        try:
            make_hubspot_request("PATCH", update_url, {"properties": deal_properties})
            logger.info("Successfully updated existing HubSpot deal %s for submission %s", deal_id, submission_id)
        except Exception as e:
            logger.error("Failed to update existing HubSpot deal %s: %s", deal_id, e)
            raise RuntimeError(f"HubSpot deal update failed: {e}") from e
    else:
        create_url = "https://api.hubapi.com/crm/v3/objects/deals"
        try:
            deal_res = make_hubspot_request("POST", create_url, {"properties": deal_properties})
            deal_id = deal_res.get("id")
            if not deal_id:
                raise RuntimeError("HubSpot deal creation succeeded without returning an id")
            logger.info("Successfully created new HubSpot deal %s for submission %s", deal_id, submission_id)
        except requests.exceptions.Timeout as te:
            logger.error(
                "HubSpot deal creation timed out for submission %s. The deal may exist remotely.",
                submission_id
            )
            raise RuntimeError(
                f"HubSpot deal creation timed out for submission {submission_id}. "
                "Idempotency search will reconcile on retry."
            ) from te
        except Exception as e:
            logger.error(f"Failed to create HubSpot Deal for submission {submission_id}: {e}")
            raise RuntimeError(f"HubSpot Deal creation failed: {e}") from e

    # 4. Associate Deal to Contact
    if deal_id and contact_id:
        try:
            association_url = f"https://api.hubapi.com/crm/v3/objects/deals/{deal_id}/associations/contacts/{contact_id}/3"
            make_hubspot_request("PUT", association_url)
            logger.info("HubSpot association complete [deal=%s, contact=%s] for submission %s", deal_id, contact_id, submission_id)
        except Exception as e:
            logger.error("Failed to associate deal %s with contact %s: %s", deal_id, contact_id, e)
            raise RuntimeError(f"HubSpot deal-contact association failed: {e}") from e

    return {
        "status": "SYNCED",
        "deal_id": deal_id,
        "contact_id": contact_id
    }

```

#### `app/services/dashboard_service.py`

```python
"""
dashboard_service.py — Super Admin Operations & Worker Performance Dashboard.
Aggregates ingestion queue stats, processing latency, and worker fleet status.
Caches snapshot for 2 minutes in memory and in the dashboard_snapshot table.
"""
import time
import json
import logging
from datetime import datetime, timezone
from decimal import Decimal
from typing import Dict, Any, Optional
import psycopg2.extras
from app.core.database import get_db_connection

logger = logging.getLogger("dashboard_service")

# In-memory snapshot cache for single-process fast path
_MEMORY_CACHE = {
    "data": None,
    "cached_at": 0.0,
    "ttl": 120.0  # 2 minutes in seconds
}

def _json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, (datetime,)):
        return obj.isoformat()
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def _format_duration(seconds: Optional[float]) -> str:
    """Format seconds into readable human-friendly duration string."""
    if seconds is None:
        return "None"
    s = int(round(seconds))
    if s < 60:
        return f"{s}s"
    m = s // 60
    rem_s = s % 60
    if m < 60:
        return f"{m}m {rem_s}s"
    h = m // 60
    rem_m = m % 60
    return f"{h}h {rem_m}m"


def compute_fresh_dashboard_stats() -> Dict[str, Any]:
    """
    Executes aggregate queries against raw_submissions and workers to generate
    a comprehensive system operational snapshot.
    Uses grouped queries and indexed scans for sub-millisecond execution.
    """
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. Request Overview: Single grouped query (GROUP BY status)
            cur.execute("""
                SELECT status, COUNT(*) as count
                FROM raw_submissions
                GROUP BY status;
            """)
            status_rows = cur.fetchall()

            status_map = {
                "pending": 0,       # RECEIVED, PENDING
                "in_progress": 0,   # PROCESSING, RETRYING
                "completed": 0,     # COMPLETED
                "failed": 0         # FAILED, DEAD_LETTERED
            }
            raw_breakdown = {}
            total_requests = 0

            for r in status_rows:
                st = (r["status"] or "").upper()
                c = int(r["count"])
                total_requests += c
                raw_breakdown[st] = c

                if st in ("RECEIVED", "PENDING"):
                    status_map["pending"] += c
                elif st in ("PROCESSING", "RETRYING"):
                    status_map["in_progress"] += c
                elif st in ("COMPLETED",):
                    status_map["completed"] += c
                elif st in ("FAILED", "DEAD_LETTERED"):
                    status_map["failed"] += c
                else:
                    status_map["pending"] += c

            # 2. Request Analytics: Success vs. Failure Rate
            finalized_total = status_map["completed"] + status_map["failed"]
            if finalized_total > 0:
                success_rate = round((status_map["completed"] / finalized_total) * 100.0, 1)
                failure_rate = round((status_map["failed"] / finalized_total) * 100.0, 1)
            else:
                success_rate = 100.0 if status_map["completed"] > 0 else 0.0
                failure_rate = 0.0

            # 3. Request Analytics: Average processing time (actual worker execution duration)
            cur.execute("""
                SELECT AVG(EXTRACT(EPOCH FROM (processing_completed_at - processing_started_at))) as avg_seconds
                FROM raw_submissions
                WHERE status = 'COMPLETED'
                  AND processing_started_at IS NOT NULL
                  AND processing_completed_at IS NOT NULL
                  AND processing_completed_at >= processing_started_at
                  AND (processing_completed_at - processing_started_at) < INTERVAL '5 minutes'
                  AND processing_completed_at >= NOW() - INTERVAL '24 hours';
            """)
            avg_row = cur.fetchone()
            avg_proc_seconds = float(avg_row["avg_seconds"]) if avg_row and avg_row["avg_seconds"] is not None else 0.0

            # 4. Request Analytics: Oldest pending request (waiting time)
            cur.execute("""
                SELECT submission_id, created_at,
                       EXTRACT(EPOCH FROM (NOW() - created_at)) AS waiting_seconds
                FROM raw_submissions
                WHERE status IN ('RECEIVED', 'PENDING')
                ORDER BY created_at ASC
                LIMIT 1;
            """)
            oldest_row = cur.fetchone()
            oldest_pending = None
            if oldest_row:
                wait_sec = float(oldest_row["waiting_seconds"]) if oldest_row["waiting_seconds"] else 0.0
                oldest_pending = {
                    "submission_id": str(oldest_row["submission_id"]),
                    "created_at": oldest_row["created_at"].isoformat() if oldest_row["created_at"] else None,
                    "waiting_seconds": round(wait_sec, 1),
                    "waiting_time_formatted": _format_duration(wait_sec)
                }

            # 5. Request Analytics: Requests over time (Hourly, last 24 hours)
            cur.execute("""
                SELECT date_trunc('hour', created_at) AS bucket, COUNT(*) as count
                FROM raw_submissions
                WHERE created_at >= NOW() - INTERVAL '24 hours'
                GROUP BY bucket
                ORDER BY bucket ASC;
            """)
            hourly_rows = cur.fetchall()
            hourly_timeline = [
                {
                    "bucket": r["bucket"].strftime("%Y-%m-%d %H:00") if r["bucket"] else "",
                    "label": r["bucket"].strftime("%H:00") if r["bucket"] else "",
                    "count": int(r["count"])
                }
                for r in hourly_rows
            ]

            # 6. Request Analytics: Requests over time (Daily, last 7 days)
            cur.execute("""
                SELECT date_trunc('day', created_at) AS bucket, COUNT(*) as count
                FROM raw_submissions
                WHERE created_at >= NOW() - INTERVAL '7 days'
                GROUP BY bucket
                ORDER BY bucket ASC;
            """)
            daily_rows = cur.fetchall()
            daily_timeline = [
                {
                    "bucket": r["bucket"].strftime("%Y-%m-%d") if r["bucket"] else "",
                    "label": r["bucket"].strftime("%b %d") if r["bucket"] else "",
                    "count": int(r["count"])
                }
                for r in daily_rows
            ]

            # 7. Worker Progress: Fleet monitoring & offline detection (> 3 minutes)
            cur.execute("""
                SELECT worker_id, worker_type, status, current_task,
                       jobs_completed, started_at, last_heartbeat,
                       EXTRACT(EPOCH FROM (NOW() - last_heartbeat)) AS seconds_since_heartbeat
                FROM workers
                ORDER BY last_heartbeat DESC;
            """)
            worker_rows = cur.fetchall()

            worker_list = []
            active_count = 0
            idle_count = 0
            offline_count = 0

            for w in worker_rows:
                sec_since = float(w["seconds_since_heartbeat"]) if w["seconds_since_heartbeat"] is not None else 999999.0
                raw_st = (w["status"] or "idle").lower()

                # Requirement 3: A worker is marked offline if its last heartbeat is older than 3 minutes (180s)
                if sec_since > 180.0:
                    effective_status = "offline"
                    offline_count += 1
                elif raw_st == "active":
                    effective_status = "active"
                    active_count += 1
                else:
                    effective_status = "idle"
                    idle_count += 1

                worker_list.append({
                    "worker_id": w["worker_id"],
                    "worker_type": w["worker_type"],
                    "status": effective_status,
                    "current_task": w["current_task"] or "None",
                    "jobs_completed": int(w["jobs_completed"] or 0),
                    "started_at": w["started_at"].isoformat() if w["started_at"] else None,
                    "last_heartbeat": w["last_heartbeat"].isoformat() if w["last_heartbeat"] else None,
                    "seconds_since_heartbeat": round(sec_since, 1),
                    "last_heartbeat_formatted": f"{int(sec_since)}s ago" if sec_since < 60 else f"{int(sec_since // 60)}m ago"
                })

            total_workers = len(worker_list)

    now_utc = datetime.now(timezone.utc)

    snapshot_data = {
        "timestamp": now_utc.isoformat(),
        "cache_ttl_seconds": 120,
        "request_overview": {
            "total_requests": total_requests,
            "pending": status_map["pending"],
            "in_progress": status_map["in_progress"],
            "completed": status_map["completed"],
            "failed": status_map["failed"],
            "raw_breakdown": raw_breakdown
        },
        "analytics": {
            "success_rate": success_rate,
            "failure_rate": failure_rate,
            "average_processing_time_seconds": round(avg_proc_seconds, 3),
            "average_processing_time_formatted": f"{round(avg_proc_seconds * 1000)}ms" if avg_proc_seconds < 1.0 else f"{round(avg_proc_seconds, 2)}s",
            "oldest_pending_request": oldest_pending,
            "hourly_timeline_24h": hourly_timeline,
            "daily_timeline_7d": daily_timeline
        },
        "worker_progress": {
            "total_workers": total_workers,
            "active_workers": active_count,
            "idle_workers": idle_count,
            "offline_workers": offline_count,
            "workers": worker_list
        }
    }

    return snapshot_data


def get_dashboard_snapshot(force_refresh: bool = False) -> Dict[str, Any]:
    """
    Returns the Super Admin operations dashboard snapshot.
    Guarantees that database stats are NOT queried on every page load:
    1. Returns in-memory cache if < 2 minutes old.
    2. Returns database `dashboard_snapshot` row if < 2 minutes old.
    3. If expired, computes snapshot once, updates table and in-memory cache, and returns.
    """
    now_monotonic = time.monotonic()

    # 1. Fast in-memory check
    if not force_refresh and _MEMORY_CACHE["data"] is not None:
        if now_monotonic - _MEMORY_CACHE["cached_at"] < _MEMORY_CACHE["ttl"]:
            return _MEMORY_CACHE["data"]

    # 2. Check persistent one-row snapshot table in database
    if not force_refresh:
        try:
            with get_db_connection() as conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("""
                        SELECT data, updated_at,
                               EXTRACT(EPOCH FROM (NOW() - updated_at)) AS age_seconds
                        FROM dashboard_snapshot
                        WHERE id = 1;
                    """)
                    row = cur.fetchone()
                    if row and row.get("data") and row.get("age_seconds") is not None:
                        age = float(row["age_seconds"])
                        if age < 120.0:  # Valid within 2 minutes
                            data = row["data"]
                            if isinstance(data, str):
                                data = json.loads(data)
                            data["cached_at_db"] = row["updated_at"].isoformat() if row["updated_at"] else None
                            data["age_seconds"] = round(age, 1)

                            # Populate local memory cache
                            _MEMORY_CACHE["data"] = data
                            _MEMORY_CACHE["cached_at"] = now_monotonic
                            return data
        except Exception as e:
            logger.warning("Could not read dashboard_snapshot from database: %s", e)

    # 3. Compute fresh aggregate statistics
    fresh_data = compute_fresh_dashboard_stats()

    # 4. Save to persistent snapshot table (UPSERT one row)
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute("""
                        INSERT INTO dashboard_snapshot (id, data, updated_at)
                        VALUES (1, %s::jsonb, NOW())
                        ON CONFLICT (id) DO UPDATE SET
                            data = EXCLUDED.data,
                            updated_at = EXCLUDED.updated_at;
                    """, (json.dumps(fresh_data, default=_json_serial),))
    except Exception as e:
        logger.error("Failed to persist dashboard_snapshot: %s", e)

    # 5. Store in memory cache
    _MEMORY_CACHE["data"] = fresh_data
    _MEMORY_CACHE["cached_at"] = now_monotonic

    return fresh_data


```

#### `app/services/email_policy_service.py`

```python
"""
email_policy_service.py — Corporate Email Eligibility Verification Service
Validates email syntax and verifies eligibility against an in-memory blocklist
of free, personal, and disposable email providers.
Accepts all valid corporate domains without requiring OTP, mailbox authentication,
or database lookups.
"""

import logging
import os
import re
from typing import Any, Optional

logger = logging.getLogger(__name__)

# RFC 5322 compliant simplified email validation regex
EMAIL_REGEX = re.compile(
    r"^[a-zA-Z0-9.!#$%&'*+/=?^_`{|}~-]+@[a-zA-Z0-9] (?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9] (?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$"
)

# Comprehensive set of known personal, consumer, and disposable email providers.
# Stored as an in-memory set for O(1) instantaneous lookups (<0.01 ms).
PERSONAL_EMAIL_DOMAINS: set[str] = {
    # Google
    "gmail.com",
    "googlemail.com",
    # Microsoft Consumer
    "outlook.com",
    "hotmail.com",
    "live.com",
    "msn.com",
    "passport.com",
    "windowslive.com",
    "hotmail.co.uk",
    "hotmail.fr",
    "hotmail.de",
    "hotmail.es",
    "hotmail.it",
    "outlook.co.uk",
    "outlook.fr",
    "outlook.de",
    "outlook.in",
    # Yahoo Consumer
    "yahoo.com",
    "ymail.com",
    "rocketmail.com",
    "yahoo.co.in",
    "yahoo.co.uk",
    "yahoo.ca",
    "yahoo.com.au",
    "yahoo.fr",
    "yahoo.de",
    "yahoo.es",
    "yahoo.it",
    "yahoo.co.jp",
    # Apple Consumer
    "icloud.com",
    "me.com",
    "mac.com",
    # AOL
    "aol.com",
    "aim.com",
    # Privacy / Freemium Webmail
    "proton.me",
    "protonmail.com",
    "pm.me",
    "tutanota.com",
    "tutamail.com",
    "tuta.io",
    "duck.com",
    # Other Global Consumer Providers
    "zoho.com",  # Personal consumer Zoho accounts; corporate Zoho uses custom domains
    "mail.com",
    "email.com",
    "usa.com",
    "post.com",
    "dr.com",
    "consultant.com",
    "gmx.com",
    "gmx.net",
    "gmx.de",
    "web.de",
    "yandex.com",
    "yandex.ru",
    "ya.ru",
    "rediffmail.com",
    "rediff.com",
    "inbox.com",
    "fastmail.com",
    "lycos.com",
    # Disposable / Temporary Mail
    "mailinator.com",
    "guerrillamail.com",
    "guerrillamail.net",
    "guerrillamail.biz",
    "guerrillamail.org",
    "sharklasers.com",
    "grr.la",
    "10minutemail.com",
    "tempmail.com",
    "throwawaymail.com",
    "trashmail.com",
    "dispostable.com",
    "yopmail.com",
    "yopmail.fr",
    "yopmail.net",
}

# Optional environment variable extension for operators
_extra_blocked = os.environ.get("NIWI_BLOCKED_EMAIL_DOMAINS", "")
if _extra_blocked:
    for domain in _extra_blocked.split(","):
        d = domain.strip().lower()
        if d:
            PERSONAL_EMAIL_DOMAINS.add(d)


def extract_and_normalize_domain(email: str) -> Optional[str]:
    """Extracts and lowercases the domain portion from an email address."""
    if not email or "@" not in email:
        return None
    parts = email.strip().split("@")
    if len(parts) != 2:
        return None
    domain = parts[1].strip().lower()
    return domain or None


def validate_email_syntax(email: str) -> bool:
    """Validates standard email syntax."""
    if not email or not isinstance(email, str):
        return False
    email = email.strip()
    if len(email) > 254:
        return False
    return bool(EMAIL_REGEX.match(email))


def check_corporate_email_eligibility(email: str) -> dict[str, Any]:
    """
    Checks whether a supplied email address is eligible under the corporate email policy.
    Accepts any corporate domain; rejects invalid syntax and personal/disposable providers.
    Does not require mailbox verification, DNS lookups, or pre-registration.
    """
    if not email or not isinstance(email, str) or not email.strip():
        return {
            "eligible": False,
            "email_verified": False,
            "domain": None,
            "error": "Email address cannot be empty.",
        }

    clean_email = email.strip()

    if not validate_email_syntax(clean_email):
        return {
            "eligible": False,
            "email_verified": False,
            "domain": None,
            "error": "Please enter a valid email address.",
        }

    domain = extract_and_normalize_domain(clean_email)
    if not domain or "." not in domain:
        return {
            "eligible": False,
            "email_verified": False,
            "domain": domain,
            "error": "Please enter a valid email address with a valid domain name.",
        }

    # Check against personal provider blocklist
    if domain in PERSONAL_EMAIL_DOMAINS:
        return {
            "eligible": False,
            "email_verified": False,
            "domain": domain,
            "error": f"'{domain}' is a personal or free email provider. Please use your corporate work email.",
        }

    # Any other valid domain is eligible as a corporate email
    return {
        "eligible": True,
        "email_verified": False,
        "domain": domain,
    }


```

#### `app/services/filter_service.py`

```python
"""
filter_service.py — Safe server-side query builder for ServiceNow-style filter execution.

Validates filter expressions against a strict allowlist of columns and data types.
Generates parameterized SQL queries to prevent SQL injection and ensure predictable AND/OR semantics.
"""

from datetime import datetime, date
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
import re

# Strict allowlist of filterable fields, their DB column mapping, and their data type
ALLOWED_FILTER_FIELDS = {
    "company_name": {
        "column": "company_name",
        "type": "text",
        "label": "Organization Name",
    },
    "name": {
        "column": "name",
        "type": "text",
        "label": "Respondent Name",
    },
    "email": {
        "column": "email",
        "type": "text",
        "label": "Recipient Email",
    },
    "designation": {
        "column": "designation",
        "type": "text",
        "label": "Job Role / Designation",
    },
    "contact_number": {
        "column": "contact_number",
        "type": "text",
        "label": "Contact Number",
    },
    "status": {
        "column": "status",
        "type": "enum",
        "label": "Status",
        "options": ["pending", "sending", "sent", "failed"],
    },
    "overall_level": {
        "column": "overall_level",
        "type": "enum",
        "label": "Maturity Level",
        "options": [
            "Level 1 — Foundational",
            "Level 2 — Early Progress",
            "Level 3 — Developing",
        ],
    },
    "overall_avg": {
        "column": "overall_avg",
        "type": "numeric",
        "label": "Overall Score",
    },
    "lc_score": {
        "column": "lc_score",
        "type": "numeric",
        "label": "Leadership & Culture Score",
    },
    "ro_score": {
        "column": "ro_score",
        "type": "numeric",
        "label": "Recruitment & Onboarding Score",
    },
    "we_score": {
        "column": "we_score",
        "type": "numeric",
        "label": "Work Environment Score",
    },
    "be_score": {
        "column": "be_score",
        "type": "numeric",
        "label": "Built Environment Score",
    },
    "tm_score": {
        "column": "tm_score",
        "type": "numeric",
        "label": "Talent Management Score",
    },
    "ca_score": {
        "column": "ca_score",
        "type": "numeric",
        "label": "Communication & Accessibility Score",
    },
    "pc_score": {
        "column": "pc_score",
        "type": "numeric",
        "label": "Products & Customer Service Score",
    },
    "sp_score": {
        "column": "sp_score",
        "type": "numeric",
        "label": "Supply Chain & Procurement Score",
    },
    "submitted_at": {
        "column": "submitted_at",
        "type": "date",
        "label": "Sent Date & Time",
    },
    "id": {
        "column": "id",
        "type": "text",
        "label": "Submission ID",
    },
    # ── Demographics stored in answers JSONB ────────────────────────────────
    # The column value uses PostgreSQL JSONB text extraction: answers->>'key'
    # All text/enum operators work correctly against these expressions.
    "function": {
        "column": "answers->>'function'",
        "type": "enum",
        "label": "Function / Department",
        "options": [
            "Administration", "Engineering", "ESG / Sustainability", "Finance",
            "HR / People", "Legal & Compliance", "Manufacturing / Production",
            "Marketing & Communications", "Operations", "Project Management",
            "Quality Assurance / Quality Control", "Research & Development (R&D)",
            "Sales & Business Development", "Supply Chain / Procurement / Logistics",
            "Technology / IT / Product Management", "Other",
        ],
    },
    "role": {
        "column": "answers->>'role'",
        "type": "enum",
        "label": "Role Level",
        "options": [
            "Individual Contributor / Team Member",
            "People Manager/Supervisor",
            "Head of Function/Director",
            "VP / Senior Leader",
            "C-Suite / Executive",
            "Board Member / Trustee",
            "Consultant / Advisor",
            "Other",
        ],
    },
    "country": {
        "column": "answers->>'country'",
        "type": "text",
        "label": "Country",
    },
    "state_ut": {
        "column": "answers->>'state_ut'",
        "type": "text",
        "label": "State / UT (India)",
    },
    "gender": {
        "column": "answers->>'gender'",
        "type": "enum",
        "label": "Gender Identity",
        "options": [
            "Man", "Woman", "Non-binary / Gender non-conforming",
            "Prefer not to say", "Other gender identity",
        ],
    },
    "is_pwd": {
        "column": "answers->>'is_pwd'",
        "type": "enum",
        "label": "Person with Disability (PwD)",
        "options": ["Yes", "No", "Prefer not to say"],
    },
    "is_neurodivergent": {
        "column": "answers->>'is_neurodivergent'",
        "type": "enum",
        "label": "Neurodivergent",
        "options": ["Yes", "No", "Prefer not to say"],
    },
    "is_marginalized": {
        "column": "answers->>'is_marginalized'",
        "type": "enum",
        "label": "Underrepresented / Marginalized",
        "options": ["Yes", "No", "Prefer not to say"],
    },
    "submission_source": {
        "column": "submission_source",
        "type": "enum",
        "label": "Submission Method",
        "options": ["DIRECT", "INVITATION"],
    },
    "organization_id": {
        "column": "organization_id",
        "type": "text",
        "label": "Organization ID",
    },
}

ALLOWED_SORT_FIELDS = set(ALLOWED_FILTER_FIELDS.keys())

ALLOWED_OPERATORS = {
    "text": {
        "is",
        "is_not",
        "contains",
        "does_not_contain",
        "starts_with",
        "ends_with",
        "is_empty",
        "is_not_empty",
    },
    "enum": {
        "is",
        "is_not",
        "is_one_of",
        "is_not_one_of",
        "is_empty",
        "is_not_empty",
    },
    "numeric": {
        "equals",
        "does_not_equal",
        "greater_than",
        "less_than",
        "greater_than_or_equal",
        "less_than_or_equal",
        "between",
        "is_empty",
        "is_not_empty",
    },
    "date": {
        "is",
        "is_before",
        "is_after",
        "is_on_or_before",
        "is_on_or_after",
        "between",
        "is_empty",
        "is_not_empty",
    },
}


def _validate_date_str(val: str) -> str:
    """Validate and sanitize YYYY-MM-DD date string."""
    if not isinstance(val, str):
        raise ValueError("Date value must be a string in YYYY-MM-DD format")
    val = val.strip()
    # Accept ISO strings or standard date formats
    m = re.match(r"^(\d{4}-\d{2}-\d{2})", val)
    if not m:
        raise ValueError(f"Invalid date format: '{val}'. Expected YYYY-MM-DD")
    try:
        datetime.strptime(m.group(1), "%Y-%m-%d")
    except ValueError as e:
        raise ValueError(f"Invalid calendar date '{val}': {e}")
    return m.group(1)


def _validate_numeric(val: Any) -> float:
    """Validate numeric input."""
    try:
        return float(val)
    except (ValueError, TypeError):
        raise ValueError(f"Invalid numeric value: '{val}'")


def build_condition_sql(condition: Dict[str, Any]) -> Tuple[str, List[Any], str]:
    """
    Build SQL clause, parameter list, and readable summary for a single condition.
    Returns: (sql_fragment, params, human_readable_summary)
    """
    field_key = condition.get("field")
    if not field_key or field_key not in ALLOWED_FILTER_FIELDS:
        raise ValueError(f"Unsupported or invalid filter field: '{field_key}'")

    meta = ALLOWED_FILTER_FIELDS[field_key]
    col = meta["column"]
    data_type = meta["type"]
    label = meta["label"]

    raw_op = condition.get("operator", "is")
    # Normalize operator string (replace spaces or hyphens with underscores)
    op = raw_op.lower().replace(" ", "_").replace("-", "_")

    # Map aliases
    if op == "equal" or op == "equals":
        op = "equals" if data_type == "numeric" else "is"
    elif op == "not_equal" or op == "does_not_equal":
        op = "does_not_equal" if data_type == "numeric" else "is_not"

    if op not in ALLOWED_OPERATORS.get(data_type, set()):
        raise ValueError(f"Operator '{raw_op}' is not valid for field '{field_key}' ({data_type})")

    val = condition.get("value")
    val_to = condition.get("value_to")
    vals = condition.get("values") or []

    # 1. Empty / Not Empty
    if op == "is_empty":
        if data_type in ("text", "enum"):
            return f"({col} IS NULL OR TRIM(CAST({col} AS TEXT)) = '')", [], f"{label} is empty"
        else:
            return f"({col} IS NULL)", [], f"{label} is empty"

    if op == "is_not_empty":
        if data_type in ("text", "enum"):
            return f"({col} IS NOT NULL AND TRIM(CAST({col} AS TEXT)) != '')", [], f"{label} is not empty"
        else:
            return f"({col} IS NOT NULL)", [], f"{label} is not empty"

    # 2. Text fields
    if data_type == "text":
        str_val = str(val or "").strip()
        if op == "is":
            return f"{col} = %s", [str_val], f"{label} is \"{str_val}\""
        elif op == "is_not":
            return f"({col} != %s OR {col} IS NULL)", [str_val], f"{label} is not \"{str_val}\""
        elif op == "contains":
            return f"{col} ILIKE %s", [f"%{str_val}%"], f"{label} contains \"{str_val}\""
        elif op == "does_not_contain":
            return f"({col} NOT ILIKE %s OR {col} IS NULL)", [f"%{str_val}%"], f"{label} does not contain \"{str_val}\""
        elif op == "starts_with":
            return f"{col} ILIKE %s", [f"{str_val}%"], f"{label} starts with \"{str_val}\""
        elif op == "ends_with":
            return f"{col} ILIKE %s", [f"%{str_val}"], f"{label} ends with \"{str_val}\""

    # 3. Enumerated fields
    if data_type == "enum":
        if op == "is":
            str_val = str(val or "").strip()
            return f"{col} = %s", [str_val], f"{label} is \"{str_val}\""
        elif op == "is_not":
            str_val = str(val or "").strip()
            return f"({col} != %s OR {col} IS NULL)", [str_val], f"{label} is not \"{str_val}\""
        elif op in ("is_one_of", "is_not_one_of"):
            clean_vals = [str(v).strip() for v in vals if str(v).strip()]
            if not clean_vals and val:
                clean_vals = [v.strip() for v in str(val).split(",") if v.strip()]
            if not clean_vals:
                raise ValueError(f"Operator '{op}' requires at least one selected value.")
            
            placeholders = ", ".join(["%s"] * len(clean_vals))
            joined_str = ", ".join(clean_vals)
            if op == "is_one_of":
                return f"{col} IN ({placeholders})", clean_vals, f"{label} is one of ({joined_str})"
            else:
                return f"({col} NOT IN ({placeholders}) OR {col} IS NULL)", clean_vals, f"{label} is not one of ({joined_str})"

    # 4. Numeric fields
    if data_type == "numeric":
        if op == "between":
            if val is None or val_to is None:
                raise ValueError("Between operator requires both minimum and maximum values.")
            n1 = _validate_numeric(val)
            n2 = _validate_numeric(val_to)
            low, high = min(n1, n2), max(n1, n2)
            return f"{col} BETWEEN %s AND %s", [low, high], f"{label} between {low} and {high}"
        
        num_val = _validate_numeric(val)
        op_map = {
            "equals": ("=", "equals"),
            "does_not_equal": ("!=", "does not equal"),
            "greater_than": (">", "greater than"),
            "less_than": ("<", "less than"),
            "greater_than_or_equal": (">=", "greater than or equal to"),
            "less_than_or_equal": ("<=", "less than or equal to"),
        }
        sql_sym, desc = op_map[op]
        if op == "does_not_equal":
            return f"({col} != %s OR {col} IS NULL)", [num_val], f"{label} {desc} {num_val}"
        return f"{col} {sql_sym} %s", [num_val], f"{label} {desc} {num_val}"

    # 5. Date fields
    if data_type == "date":
        if op == "between":
            if not val or not val_to:
                raise ValueError("Between operator requires both start date and end date.")
            d1 = _validate_date_str(str(val))
            d2 = _validate_date_str(str(val_to))
            d_start, d_end = min(d1, d2), max(d1, d2)
            return f"DATE({col}) BETWEEN %s AND %s", [d_start, d_end], f"{label} between {d_start} and {d_end}"

        d_val = _validate_date_str(str(val))
        date_op_map = {
            "is": ("=", "is"),
            "is_before": ("<", "is before"),
            "is_after": (">", "is after"),
            "is_on_or_before": ("<=", "is on or before"),
            "is_on_or_after": (">=", "is on or after"),
        }
        sql_sym, desc = date_op_map[op]
        return f"DATE({col}) {sql_sym} %s", [d_val], f"{label} {desc} {d_val}"

    raise ValueError(f"Unhandled condition for field '{field_key}' with operator '{op}'")


def build_filter_query(
    filter_groups: Optional[List[Dict[str, Any]]] = None,
    sort_by: Optional[List[Dict[str, str]]] = None,
    page: int = 1,
    per_page: int = 10,
    organization_id: Optional[str] = None,
) -> Tuple[str, str, List[Any], str]:
    """
    Build parameterized SQL queries for data fetching and counting.
    Returns:
        (data_sql, count_sql, parameters, readable_summary)
    """
    params: List[Any] = []
    top_clauses: List[str] = []
    summary_parts: List[str] = []

    # Enforce organization isolation if provided
    if organization_id:
        top_clauses.append("organization_id = %s")
        params.append(str(organization_id))
        summary_parts.append(f"Organization ID = {organization_id}")

    # Process filter groups
    if filter_groups:
        for g_idx, group in enumerate(filter_groups):
            raw_log_op = group.get("logical_operator", "AND").upper()
            log_op = "OR" if raw_log_op == "OR" else "AND"
            conditions = group.get("conditions", [])

            group_clauses: List[str] = []
            group_summaries: List[str] = []

            for cond in conditions:
                sql_frag, cond_params, cond_sum = build_condition_sql(cond)
                group_clauses.append(sql_frag)
                params.extend(cond_params)
                group_summaries.append(cond_sum)

            if group_clauses:
                glue = f" {log_op} "
                summary_glue = f" .{log_op.lower()}. "
                
                joined_group = glue.join(group_clauses)
                if len(group_clauses) > 1:
                    joined_group = f"({joined_group})"
                top_clauses.append(joined_group)

                joined_summary = summary_glue.join(group_summaries)
                if len(group_summaries) > 1 and len(filter_groups) > 1:
                    joined_summary = f"({joined_summary})"
                summary_parts.append(joined_summary)

    where_sql = ""
    if top_clauses:
        where_sql = "WHERE " + " AND ".join(top_clauses)

    readable_summary = "All"
    if summary_parts:
        readable_summary = "All > " + " .and. ".join(summary_parts)

    # Count query
    count_sql = f"SELECT COUNT(*) FROM submissions {where_sql}"

    # Sort query construction
    sort_clauses: List[str] = []
    if sort_by:
        for s in sort_by:
            s_field = s.get("field")
            if s_field and s_field in ALLOWED_SORT_FIELDS:
                col_name = ALLOWED_FILTER_FIELDS[s_field]["column"]
                dir_str = "ASC" if str(s.get("direction", "")).lower() == "asc" else "DESC"
                sort_clauses.append(f"{col_name} {dir_str} NULLS LAST")

    # Deterministic s
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `app/services/org_cache_service.py`

```python
"""
org_cache_service.py — High-Performance In-Memory Organisation Registry Cache
Provides sub-millisecond organisation lookups, thread-safe atomic snapshots,
a scheduled 30-minute refresh loop, multi-worker invalidation synchronization,
and negative lookup caching to protect PostgreSQL connection pools under load.
"""

import asyncio
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

from cachetools import TTLCache
import psycopg2.extras

from app.core.database import get_db_connection

logger = logging.getLogger(__name__)

# Concurrency lock for atomic cache replacement and metric tracking
_lock = threading.RLock()

# In-memory lookup dictionaries:
# _orgs_by_normalized_name: normalized_name -> dict(id, name, is_active, is_deleted, approval_status, updated_at)
# _orgs_by_id: str(id) -> dict(...)
_orgs_by_normalized_name: dict[str, dict[str, Any]] = {}
_orgs_by_id: dict[str, dict[str, Any]] = {}

# Negative lookup cache with 30s TTL to prevent DB connection exhaustion from bursts of invalid lookups
_negative_cache: TTLCache = TTLCache(maxsize=2000, ttl=30.0)

# Metadata and performance diagnostics
_last_refresh_timestamp: float = 0.0
_last_refresh_datetime: Optional[datetime] = None
_last_refresh_duration_ms: float = 0.0
_cache_hits: int = 0
_cache_misses: int = 0
_negative_hits: int = 0

# Multi-worker synchronization file
INVALIDATION_FILE = Path(os.environ.get("NIWI_ORG_CACHE_INVALIDATION_FILE", "/tmp/niwi_org_cache_version"))
_last_seen_invalidation_mtime_ns: int = 0

# Background scheduled task reference
_background_task: Optional[asyncio.Task] = None
_background_thread: Optional[threading.Thread] = None
_stop_event = threading.Event()


def normalize_org_name(name: str) -> str:
    """Case-insensitive and whitespace-normalized name representation."""
    if not name:
        return ""
    return " ".join(name.strip().lower().split())


def _touch_invalidation_file() -> None:
    """Updates the mtime of the invalidation file so other workers detect the change."""
    global _last_seen_invalidation_mtime_ns
    try:
        INVALIDATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        now_ns = time.time_ns()
        with open(INVALIDATION_FILE, "w") as f:
            f.write(str(now_ns))
        stat_res = INVALIDATION_FILE.stat()
        _last_seen_invalidation_mtime_ns = stat_res.st_mtime_ns
    except Exception as e:
        logger.warning("Failed to touch cache invalidation file %s: %s", INVALIDATION_FILE, e)


def _check_interprocess_invalidation() -> None:
    """
    Checks if another worker has signaled an invalidation via the invalidation file.
    Fast stat check on local tmpfs/disk takes <1 microsecond.
    """
    global _last_seen_invalidation_mtime_ns
    try:
        if INVALIDATION_FILE.exists():
            stat_res = INVALIDATION_FILE.stat()
            if stat_res.st_mtime_ns > _last_seen_invalidation_mtime_ns:
                logger.info(
                    "Detected cross-worker organisation cache invalidation (mtime %s > %s). Reloading...",
                    stat_res.st_mtime_ns,
                    _last_seen_invalidation_mtime_ns,
                )
                refresh_org_cache()
    except Exception as e:
        logger.warning("Error checking inter-process cache invalidation file: %s", e)


def refresh_org_cache(conn=None) -> bool:
    """
    Atomically refreshes the in-memory organisation registry from PostgreSQL.
    Builds the new lookup snapshots in local scope first. If the database query
    fails, the last known good snapshot is preserved without interruption.
    """
    global _orgs_by_normalized_name, _orgs_by_id
    global _last_refresh_timestamp, _last_refresh_datetime, _last_refresh_duration_ms
    global _last_seen_invalidation_mtime_ns

    t0 = time.perf_counter()
    new_by_name: dict[str, dict[str, Any]] = {}
    new_by_id: dict[str, dict[str, Any]] = {}

    try:
        def _fetch(active_conn):
            with active_conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status, updated_at
                    FROM organizations
                """)
                return cur.fetchall()

        if conn is not None:
            rows = _fetch(conn)
        else:
            with get_db_connection() as active_conn:
                rows = _fetch(active_conn)

        for r in rows:
            entry = {
                "id": str(r["id"]),
                "name": r["name"],
                "is_active": bool(r["is_active"]),
                "is_deleted": bool(r["is_deleted"]),
                "approval_status": str(r["approval_status"]).lower() if r["approval_status"] else "approved",
                "updated_at": r.get("updated_at"),
            }
            norm_name = normalize_org_name(entry["name"])
            if norm_name:
                new_by_name[norm_name] = entry
            new_by_id[entry["id"]] = entry

        duration_ms = (time.perf_counter() - t0) * 1000.0

        with _lock:
            _orgs_by_normalized_name = new_by_name
            _orgs_by_id = new_by_id
            _negative_cache.clear()
            _last_refresh_timestamp = time.monotonic()
            _last_refresh_datetime = datetime.now(timezone.utc)
            _last_refresh_duration_ms = round(duration_ms, 2)
            if INVALIDATION_FILE.exists():
                try:
                    _last_seen_invalidation_mtime_ns = INVALIDATION_FILE.stat().st_mtime_ns
                except Exception:
                    pass

        logger.info(
            "Organisation cache refreshed: %d organisations indexed in %.2f ms (PID: %s)",
            len(new_by_id),
            duration_ms,
            os.getpid(),
        )
        return True

    except Exception as e:
        duration_ms = (time.perf_counter() - t0) * 1000.0
        logger.error(
            "Failed to refresh organisation cache after %.2f ms (retaining previous snapshot of %d orgs): %s",
            duration_ms,
            len(_orgs_by_id),
            e,
        )
        return False


def invalidate_org_cache() -> None:
    """
    Invalidates the organisation cache across all workers.
    Touches the invalidation file and immediately refreshes the current worker.
    """
    _touch_invalidation_file()
    refresh_org_cache()


def get_organisation_by_name(name: str) -> tuple[Optional[dict[str, Any]], str]:
    """
    Resolves an organisation by name using memory cache first, falling back to DB.
    Returns: (org_dict, source_str) where source_str is:
      - 'CACHE_HIT': Served directly from process memory (<10ms)
      - 'NEGATIVE_HIT': Recognized non-existent name from negative cache
      - 'DB_HIT': Cache miss, retrieved from PostgreSQL and cached
      - 'DB_MISS': Not found in PostgreSQL, recorded in negative cache
      - 'EMPTY': Input was empty
    """
    global _cache_hits, _cache_misses, _negative_hits

    normalized = normalize_org_name(name)
    if not normalized:
        return None, "EMPTY"

    _check_interprocess_invalidation()

    with _lock:
        if normalized in _orgs_by_normalized_name:
            _cache_hits += 1
            return _orgs_by_normalized_name[normalized], "CACHE_HIT"

        if normalized in _negative_cache:
            _negative_hits += 1
            return None, "NEGATIVE_HIT"

    # Cache miss: Fall back to authoritative PostgreSQL query
    _cache_misses += 1
    t0 = time.perf_counter()
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status, updated_at
                    FROM organizations
                    WHERE LOWER(TRIM(name)) = LOWER(TRIM(%s))
                """, (name.strip(),))
                row = cur.fetchone()

        if row:
            entry = {
                "id": str(row["id"]),
                "name": row["name"],
                "is_active": bool(row["is_active"]),
                "is_deleted": bool(row["is_deleted"]),
                "approval_status": str(row["approval_status"]).lower() if row["approval_status"] else "approved",
                "updated_at": row.get("updated_at"),
            }
            with _lock:
                _orgs_by_normalized_name[normalized] = entry
                _orgs_by_id[entry["id"]] = entry
                _negative_cache.pop(normalized, None)
            logger.info("DB fallback resolved org '%s' in %.2f ms", entry["name"], (time.perf_counter() - t0) * 1000.0)
            return entry, "DB_HIT"
        else:
            with _lock:
                _negative_cache[normalized] = True
            return None, "DB_MISS"

    except Exception as e:
        logger.error("Database fallback query failed for org '%s': %s", name, e)
        raise


def get_organisation_by_id(org_id: str | UUID) -> tuple[Optional[dict[str, Any]], str]:
    """Resolves an organisation by UUID string using memory cache first, falling back to DB."""
    global _cache_hits, _cache_misses

    if not org_id:
        return None, "EMPTY"

    org_id_str = str(org_id).strip().lower()
    _check_interprocess_invalidation()

    with _lock:
        if org_id_str in _orgs_by_id:
            _cache_hits += 1
            return _orgs_by_id[org_id_str], "CACHE_HIT"

    # Cache miss
    _cache_misses += 1
    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status, updated_at
                    FROM organizations
                    WHERE id = %s
                """, (org_id_str,))
                row = cur.fetchone()

        if row:
            entry = {
                "id": str(row["id"]),
                "name": row["name"],
                "is_active": bool(row["is_active"]),
                "is_deleted": bool(row["is_deleted"]),
                "approval_status": str(row["approval_status"]).lower() if row["approval_status"] else "approved",
                "updated_at": row.get("updated_at"),
            }
            norm_name = normalize_org_name(entry["name"])
            with _lock:
                _orgs_by_id[entry["id"]] = entry
                if norm_name:
                    _orgs_by_normalized_name[norm_name] = entry
            return entry, "DB_HIT"
        return None, "DB_MISS"
    except Exception as e:
        logger.error("Database fallback query failed for org ID '%s': %s", org_id_str, e)
        raise


def is_org_eligible(org: dict[str, Any]) -> tuple[bool, Optional[str]]:
    """
    Validates whether an organisation is currently eligible for assessments.
    Returns: (is_eligible, error_message)
    """
    if not org:
        return False, "We couldn't find this organisation. Please check the spelling or contact your administrator."
    if org.get("is_deleted"):
        return False, "This organisation has been deactivated or removed."
    if not org.get("is_active"):
        return False, "This organisation is currently inactive."
    if org.get("approval_status") != "approved":
        return False, "This organisation is pending administrative approval."
    return True, None


def get_cache_stats() -> dict[str, Any]:
    """Diagnostic metrics for health and monitoring endpoints."""
    with _lock:
        total_requests = _cache_hits + _cache_misses + _negative_hits
        hit_ratio = round((_cache_hits / total_requests * 100.0), 2) if total_requests > 0 else 0.0
        return {
            "pid": os.getpid(),
            "total_cached_orgs": len(_orgs_by_id),
            "cache_hits": _cache_hits,
            "cache_misses": _cache_misses,
            "negative_hits": _negative_hits,
            "hit_ratio_percent": hit_ratio,
            "negative_cache_size": len(_negative_cache),
            "last_refresh_utc": _last_refresh_datetime.isoformat() if _last_refresh_datetime else None,
            "last_refresh_duration_ms": _last_refresh_duration_ms,
        }


def _run_scheduled_refresh_thread(interval_seconds: int):
    """Background worker thread executing periodic refreshes every interval_seconds (default 30m)."""
    logger.info("Organisation cache background refresh thread started (interval=%ds)", interval_seconds)
    while not _stop_event.is_set():
        if _stop_event.wait(timeout=interval_seconds):
            break
        try:
            refresh_org_cache()
        except Exception as e:
            logger.error("Periodic organisation cache refresh encountered an error: %s", e)
    logger.info("Organisation cache background refresh thread stopped")


def start_org_cache_refresher(interval_seconds: int = 1800) -> None:
    """Starts the background scheduled refresh (default 1800s = 30 minutes)."""
    global _background_thread, _stop_event
    with _lock:
        if _background_thread is not None and _background_thread.is_alive():
            return
        _stop_event.clear()
        _background_thread = threading.Thread(
            target=_run_scheduled_refresh_thread,
            args=(interval_seconds,),
            name="OrgCacheRefresher",
            daemon=True,
        )
        _background_thread.start()


def stop_org_cache_refresher() -> None:
    """Stops the background scheduled refresh."""
    global _background_thread, _stop_event
    with _lock:
        _stop_event.set()
        if _background_thread and _background_thread.is_alive():
            _background_thread.join(timeout=2.0)
            _background_thread = None


```

#### `app/services/org_scoring_service.py`

```python
"""
org_scoring_service.py — Weighted multi-respondent org scoring.

All functions are pure (no DB calls). The caller fetches the data and
passes it in; these functions just crunch numbers and build email HTML.
"""

from __future__ import annotations
import html as html_module
from typing import Any

SECTION_KEYS = ["lc", "ro", "we", "be", "tm", "ca", "pc", "sp"]
SECTION_LABELS = {
    "lc": "Leadership & Culture",
    "ro": "Recruitment & Onboarding",
    "we": "Work Environment & Adjustments",
    "be": "Built Environment & Sensory",
    "tm": "Talent Management & Development",
    "ca": "Communication & Accessibility",
    "pc": "Products & Customer Experience",
    "sp": "Suppliers & Procurement",
}

LEVEL_THRESHOLDS = [
    (0,  6,  "Level 1 — Foundational"),
    (7,  14, "Level 2 — Early Progress"),
    (15, 20, "Level 3 — Developing"),
]


def _level(score: float) -> str:
    r = round(score)
    if r <= 6:
        return "Level 1 — Foundational"
    elif r <= 14:
        return "Level 2 — Early Progress"
    else:
        return "Level 3 — Developing"


def calc_weighted_org_score(links: list[dict[str, Any]]) -> dict[str, Any] | None:
    """
    links — list of dicts, each containing:
        overall_avg   float
        weight        float
        lc_score … sp_score  int
        name, email, designation, submitted_at, id  (passed through)

    Returns a dict with:
        org_avg         float
        org_level       str
        respondent_count int
        section_avgs    {lc: float, ro: float, …}
        section_levels  {lc: str, …}
        respondents     list (original links, enriched with weighted_contribution %)
    """
    if not links:
        return None

    total_weight = sum(float(l.get("weight", 1.0)) for l in links)
    if total_weight == 0:
        return None

    org_avg = sum(
        float(l.get("overall_avg") or 0) * float(l.get("weight", 1.0))
        for l in links
    ) / total_weight

    section_avgs: dict[str, float] = {}
    for key in SECTION_KEYS:
        col = f"{key}_score"
        section_avgs[key] = sum(
            float(l.get(col) or 0) * float(l.get("weight", 1.0))
            for l in links
        ) / total_weight

    section_levels = {k: _level(v) for k, v in section_avgs.items()}

    # Enrich each respondent with their weighted contribution %
    respondents = []
    for l in links:
        w = float(l.get("weight", 1.0))
        respondents.append({
            **l,
            "weighted_contribution_pct": round((w / total_weight) * 100, 1),
        })

    return {
        "org_avg": round(org_avg, 2),
        "org_level": _level(org_avg),
        "respondent_count": len(links),
        "total_weight": total_weight,
        "section_avgs": {k: round(v, 2) for k, v in section_avgs.items()},
        "section_levels": section_levels,
        "respondents": respondents,
    }


def build_org_summary_email(
    org_name: str,
    scores: dict[str, Any],
    respondents: list[dict[str, Any]],
) -> str:
    """
    Build the HTML body for the org summary email.
    scores — output of calc_weighted_org_score()
    respondents — same list (already inside scores["respondents"])
    """

    def _e(v: Any) -> str:
        return html_module.escape(str(v)) if v is not None else ""

    org_avg   = scores["org_avg"]
    org_level = scores["org_level"]
    sec_avgs  = scores["section_avgs"]
    sec_lvls  = scores["section_levels"]

    # Respondent rows
    respondent_rows = ""
    for r in respondents:
        respondent_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;">{_e(r.get('name'))}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;color:#666;">{_e(r.get('designation'))}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;font-weight:700;">
            {_e(r.get('overall_avg'))}/20
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;color:#666;">
            {_e(r.get('weight'))}×
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;color:#009070;font-weight:600;">
            {_e(r.get('weighted_contribution_pct'))}%
          </td>
        </tr>"""

    # Section rows
    section_rows = ""
    for key in SECTION_KEYS:
        label = SECTION_LABELS[key]
        avg   = sec_avgs.get(key, 0)
        lvl   = sec_lvls.get(key, "")
        bar_w = min(int((avg / 20) * 100), 100)
        section_rows += f"""
        <tr>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;font-weight:600;">{_e(label)}</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;text-align:center;font-weight:700;">{avg}/20</td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;">
            <div style="background:#E2DDD4;border-radius:4px;height:8px;width:100%;">
              <div style="background:#009070;border-radius:4px;height:8px;width:{bar_w}%;"></div>
            </div>
          </td>
          <td style="padding:10px 12px;border-bottom:1px solid #E2DDD4;color:#666;font-size:0.85em;">{_e(lvl)}</td>
        </tr>"""

    return f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width,initial-scale=1.0">
  <title>NeuroMark Org Summary — {_e(org_name)}</title>
</head>
<body style="margin:0;padding:0;background:#F5F2EB;font-family:'DM Sans',Arial,sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0">
  <tr><td align="center" style="padding:40px 20px;">
    <table width="600" cellpadding="0" cellspacing="0" style="background:#120050;border-radius:16px 16px 0 0;">
      <tr><td style="padding:36px 40px;">
        <p style="margin:0 0 8px;font-size:11px;font-weight:700;letter-spacing:2px;color:#AFA9EC;text-transform:uppercase;">Orchvate</p>
        <h1 style="margin:0 0 6px;font-size:26px;font-weight:400;color:#FFFFFF;font-family:Georgia,serif;">
          Organisation Audit Summary
        </h1>
        <p style="margin:0;font-size:14px;color:#AFA9EC;">{_e(org_name)}</p>
      </td></tr>
    </table>

    <table width="600" cellpadding="0" cellspacing="0" style="background:#FFFFFF;border-left:1px solid #E2DDD4;border-right:1px solid #E2DDD4;">
      <!-- Overall score -->
      <tr><td style="padding:32px 40px 0;">
        <p style="margin:0 0 4px;font-size:12px;font-weight:700;text-transform:uppercase;letter-spacing:0.08em;color:#999;">Overall Weighted Score</p>
        <p style="margin:0;font-size:42px;font-weight:800;color:#120050;">{org_avg}<span style="font-size:20px;color:#999;">/20</span></p>
        <p style="margin:4px 0 0;font-size:14px;color:#009070;font-weight:700;">{_e(org_level)}</p>
      </td></tr>

      <!-- Respondents table -->
      <tr><td style="padding:28px 40px 0;">
        <p style="margin:0 0 12px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#120050;">Respondents</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <thead>
            <tr style="background:#F5F2EB;">
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Name</th>
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Role</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Score</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Weight</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Contribution</th>
            </tr>
          </thead>
          <tbody>{respondent_rows}</tbody>
        </table>
      </td></tr>

      <!-- Section breakdown -->
      <tr><td style="padding:28px 40px 0;">
        <p style="margin:0 0 12px;font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:0.06em;color:#120050;">Section Breakdown</p>
        <table width="100%" cellpadding="0" cellspacing="0" style="border-collapse:collapse;">
          <thead>
            <tr style="background:#F5F2EB;">
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Section</th>
              <th style="padding:8px 12px;text-align:center;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Avg</th>
              <th style="padding:8px 12px;font-size:11px;color:#999;width:160px;"></th>
              <th style="padding:8px 12px;text-align:left;font-size:11px;text-transform:uppercase;letter-spacing:0.06em;color:#999;">Level</th>
            </tr>
          </thead>
          <tbody>{section_rows}</tbody>
        </table>
      </td></tr>

      <tr><td style="padding:32px 40px;">
        <p style="margin:0;font-size:12px;color:#aaa;text-align:center;border-top:1px solid #E2DDD4;padding-top:20px;">
          Powered by Orchvate · NeuroMark Audit Platform
        </p>
      </td></tr>
    </table>
  </td></tr>
</table>
</body>
</html>"""

```

#### `app/services/outbox_service.py`

```python
from app.services.worker_tracker import WorkerTracker
"""
outbox_service.py — Transactional Outbox Dispatcher for Azure Service Bus.
Polls PostgreSQL service_bus_outbox table using SELECT ... FOR UPDATE SKIP LOCKED
and reliably dispatches events to Azure Service Bus with exponential backoff and lease management.
When Service Bus is not configured, yields gracefully to DB-outbox fallback worker.
"""
import os
import sys
import time
import signal
import socket
import logging
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any

from app.core.database import get_db_connection
from app.core.service_bus import publish_event, close_service_bus, is_service_bus_configured

logger = logging.getLogger("outbox_dispatcher")
if not logger.handlers:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(logging.Formatter("[%(asctime)s] [%(levelname)s] [outbox_dispatcher] %(message)s"))
    logger.addHandler(handler)
logger.setLevel(logging.INFO)

MAX_RETRIES = 5
LOCK_TIMEOUT_SECONDS = 60
DEFAULT_POLL_INTERVAL = float(os.environ.get("OUTBOX_POLL_INTERVAL", "1.0"))
BATCH_SIZE = int(os.environ.get("OUTBOX_BATCH_SIZE", "10"))

_stop_requested = False


def _signal_handler(signum, frame):
    global _stop_requested
    logger.info("Received signal %s, initiating graceful outbox dispatcher shutdown...", signum)
    _stop_requested = True


def dispatch_pending_outbox_events(batch_size: int = BATCH_SIZE, worker_id: Optional[str] = None) -> int:
    """
    Claim and dispatch pending outbox events using FOR UPDATE SKIP LOCKED.
    
    Returns:
        Number of events processed in this iteration.
    """
    if not is_service_bus_configured():
        return 0

    if worker_id is None:
        worker_id = f"outbox-{socket.gethostname()}-{os.getpid()}"

    claimed_events: List[Dict[str, Any]] = []

    # 1. Claim batch with row locks and lease timeout
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, event_type, aggregate_id, payload, attempt_count
                    FROM service_bus_outbox
                    WHERE status IN ('PENDING', 'FAILED')
                      AND next_retry_at <= NOW()
                      AND (locked_until IS NULL OR locked_until < NOW())
                    ORDER BY created_at ASC
                    LIMIT %s
                    FOR UPDATE SKIP LOCKED;
                    """,
                    (batch_size,)
                )
                rows = cur.fetchall()
                if not rows:
                    return 0

                event_ids = [r[0] for r in rows]
                cur.execute(
                    """
                    UPDATE service_bus_outbox
                    SET status = 'PROCESSING',
                        locked_until = NOW() + INTERVAL '1 second' * %s,
                        locked_by = %s
                    WHERE id = ANY(%s::uuid[])
                    """,
                    (LOCK_TIMEOUT_SECONDS, worker_id, event_ids)
                )

                for r in rows:
                    claimed_events.append({
                        "id": str(r[0]),
                        "event_type": r[1],
                        "aggregate_id": str(r[2]),
                        "payload": r[3],
                        "attempt_count": r[4],
                    })

    # 2. Dispatch each claimed event to Azure Service Bus
    for event in claimed_events:
        evt_id = event["id"]
        event_type = event["event_type"]
        aggregate_id = event["aggregate_id"]
        payload = event["payload"]
        attempt_count = event["attempt_count"]

        # User requirement: Publish submission IDs, not large payloads. MessageId = submission_id
        dispatch_payload = {
            "submission_id": str(aggregate_id),
            "event_type": event_type,
            "outbox_id": str(evt_id)
        }

        try:
            logger.info("Dispatching outbox event %s (%s) for submission %s", evt_id, event_type, aggregate_id)
            res = publish_event(
                event_type=event_type,
                aggregate_id=aggregate_id,
                payload=dispatch_payload,
                message_id=str(aggregate_id)
            )

            if res is None:
                # Service bus became unavailable or is offline
                logger.warning("Service Bus publish returned None for event %s. Reverting to PENDING.", evt_id)
                with get_db_connection() as conn:
                    with conn:
                        with conn.cursor() as cur:
                            cur.execute(
                                """
                                UPDATE service_bus_outbox
                                SET status = 'PENDING',
                                    locked_until = NULL,
                                    locked_by = NULL
                                WHERE id = %s::uuid
                                """,
                                (evt_id,)
                            )
                continue

            # Mark as PUBLISHED
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            UPDATE service_bus_outbox
                            SET status = 'PUBLISHED',
                                published_at = NOW(),
                                locked_until = NULL,
                                locked_by = NULL,
                                last_error = NULL
                            WHERE id = %s::uuid
                            """,
                            (evt_id,)
                        )
            logger.info("Successfully published outbox event %s to Service Bus", evt_id)

        except Exception as e:
            new_attempts = attempt_count + 1
            err_msg = str(e)[:1000]
            logger.error("Failed to publish outbox event %s (attempt %s/%s): %s", evt_id, new_attempts, MAX_RETRIES, err_msg)

            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        if new_attempts >= MAX_RETRIES:
                            cur.execute(
                                """
                                UPDATE service_bus_outbox
                                SET status = 'DEAD_LETTER',
                                    attempt_count = %s,
                                    locked_until = NULL,
                                    locked_by = NULL,
                                    last_error = %s
                                WHERE id = %s::uuid
                                """,
                                (new_attempts, err_msg, evt_id)
                            )
                            logger.critical("Outbox event %s moved to DEAD_LETTER after %s failed attempts", evt_id, new_attempts)
                        else:
                            backoff_seconds = 2 ** new_attempts
                            cur.execute(
                                """
                                UPDATE service_bus_outbox
                                SET status = 'FAILED',
                                    attempt_count = %s,
                                    next_retry_at = NOW() + INTERVAL '1 second' * %s,
                                    locked_until = NULL,
                                    locked_by = NULL,
                                    last_error = %s
                                WHERE id = %s::uuid
                                """,
                                (new_attempts, backoff_seconds, err_msg, evt_id)
                            )

    return len(claimed_events)




def cleanup_published_outbox_events(retention_days: int = 7, batch_size: int = 5000) -> int:
    """
    Safely prunes PUBLISHED outbox rows older than retention_days in small batches
    to avoid long-lived exclusive table locks.
    """
    total_deleted = 0
    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        WITH to_delete AS (
                            SELECT id FROM service_bus_outbox
                            WHERE status = 'PUBLISHED'
                              AND published_at < NOW() - (%s || ' days')::interval
                            LIMIT %s
                        )
                        DELETE FROM service_bus_outbox
                        WHERE id IN (SELECT id FROM to_delete);
                        """,
                        (retention_days, batch_size)
                    )
                    total_deleted = cur.rowcount
        if total_deleted > 0:
            logger.info("Cleaned up %d expired published outbox events (retention: %d days)", total_deleted, retention_days)
    except Exception as e:
        logger.error("Outbox cleanup failed: %s", e)
    return total_deleted

def run_db_maintenance_vacuum():
    """Periodic non-blocking VACUUM ANALYZE to keep Postgres statistics fresh and prune dead tuples."""
    try:
        from app.core.database import get_conn
        conn = get_conn()
        conn.autocommit = True
        with conn.cursor() as cur:
            cur.execute("VACUUM (ANALYZE) raw_submissions;")
            cur.execute("VACUUM (ANALYZE) service_bus_outbox;")
        conn.close()
        logger.info("Database automated VACUUM ANALYZE completed successfully.")
    except Exception as e:
        logger.error("Periodic VACUUM ANALYZE error: %s", e)


def check_system_health_and_alert():
    """Alert super admin if queue is backed up (>200 items for >15m) or workers are offline."""
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT COUNT(*) as pending_count,
                           EXTRACT(EPOCH FROM (NOW() - MIN(created_at))) as oldest_wait_sec
                    FROM raw_submissions
                    WHERE status IN ('RECEIVED', 'PENDING');
                    """
                )
                q_row = cur.fetchone()
                pending_count = q_row[0] or 0
                oldest_wait = q_row[1] or 0.0

                if pending_count >= 200 and oldest_wait >= 900:  # > 200 items waiting > 15 mins
                    from app.services.settings_service import get_settings, send_acs_email, get_sender_for_send, is_acs_configured
                    settings = get_settings(cur)
                    admin_email = settings.get("notification_email")
                    if admin_email and is_acs_configured():
                        sender_addr, sender_name = get_sender_for_send(cur)
                        send_acs_email(
                            to_address=admin_email,
                            subject=f"⚠️ [NIWI System Alert] Ingestion Queue Backlog High ({pending_count} pending)",
                            html=f"<p>System Alert: Ingestion queue has <strong>{pending_count}</strong> pending submissions. Oldest request waiting: {int(oldest_wait // 60)} minutes.</p>",
                            plain=f"System Alert: Ingestion queue has {pending_count} pending submissions. Oldest waiting: {int(oldest_wait // 60)} mins.",
                            sender_address=sender_addr,
                            sender_name=sender_name
                        )
                        logger.warning("Dispatched high queue backlog alert to %s", admin_email)
    except Exception as e:
        logger.error("Health check alert error: %s", e)


def run_outbox_dispatcher(poll_interval: float = DEFAULT_POLL_INTERVAL):
    """Continuous outbox dispatcher loop."""
    try:
        signal.signal(signal.SIGTERM, _signal_handler)
        signal.signal(signal.SIGINT, _signal_handler)
    except (ValueError, AttributeError):
        pass

    worker_id = f"outbox-disp-{socket.gethostname()}-{os.getpid()}"
    tracker = WorkerTracker(worker_id=worker_id, worker_type="outbox_dispatcher", heartbeat_interval=45.0)
    tracker.set_idle("Polling outbox events")
    logger.info("Outbox dispatcher daemon started [worker_id=%s, poll_interval=%.2fs]", worker_id, poll_interval)

    from app.core.database import init_connection_pool
    try:
        init_connection_pool(minconn=2, maxconn=4)
    except Exception as e:
        logger.warning("Could not initialize outbox connection pool: %s", e)

    warned_offline = False
    last_cleanup_time = time.monotonic()
    last_digest_time = time.monotonic()
    last_vacuum_time = time.monotonic()
    last_health_check_time = time.monotonic()

    while not _stop_requested:
        # 1. Periodic batch cleanup of published outbox events (every 1 hour)
        if time.monotonic() - last_cleanup_time > 3600:
            cleanup_published_outbox_events()
            last_cleanup_time = time.monotonic()

        # 2. Periodic 5-minute batched digest notification to admin
        if time.monotonic() - last_digest_time >= 300:
            try:
                from app.services.settings_service import send_admin_submission_digest
                send_admin_submission_digest()
            except Exception as d_err:
                logger.error("Failed to execute 5-minute admin digest: %s", d_err)
            last_digest_time = time.monotonic()

        # 3. Periodic 15-minute system health monitoring & alerting
        if time.monotonic() - last_health_check_time >= 900:
            check_system_health_and_alert()
            last_health_check_time = time.monotonic()

        # 4. Periodic 24-hour non-blocking database vacuum & analysis
        if time.monotonic() - last_vacuum_time >= 86400:
            run_db_maintenance_vacuum()
            last_vacuum_time = time.monotonic()

        try:
            if not is_service_bus_configured():
                if not warned_offline:
                    logger.info("Service Bus is not configured. Outbox events will be processed by DB fallback worker.")
                    warned_offline = True
                time.sleep(poll_interval * 2)
                continue
            else:
                warned_offline = False

            processed = dispatch_pending_outbox_events(batch_size=BATCH_SIZE, worker_id=worker_id)
            if processed > 0:
                tracker.record_job_completed(processed)
                tracker.set_task(f"Dispatched {processed} outbox events", status="active")
                time.sleep(0.05)  # Yield briefly under heavy load
            else:
                tracker.set_idle("Waiting for outbox events")
                tracker.heartbeat_if_due()
                time.sleep(poll_interval)
        except Exception as e:
            logger.error("Unexpected error in outbox dispatcher loop: %s", e, exc_info=True)
            time.sleep(poll_interval)

    logger.info("Outbox dispatcher daemon stopping, closing Service Bus connections...")
    close_service_bus()
    logger.info("Outbox dispatcher shutdown complete.")


if __name__ == "__main__":
    run_outbox_dispatcher()

```

#### `app/services/rate_limit_service.py`

```python
"""
rate_limit_service.py — Central Dynamic Rate Limiting & Security Configuration Service
Manages persistent, admin-configurable rate limits in PostgreSQL with in-memory caching,
instant cross-worker synchronization via version notification, trusted IP extraction,
and dynamic traffic classification (Public, Secure Link, Session Protection, Invalid Token).
"""

import inspect
import json
import logging
import os
import re
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional
from uuid import UUID

import psycopg2.extras
from limits import parse
from slowapi.errors import RateLimitExceeded
from slowapi.wrappers import Limit
from starlette.requests import Request

from app.core.database import get_db_connection
from app.core.limiter import limiter
from app.services.token_service import resolve_assessment_token

logger = logging.getLogger(__name__)

# Default rate limits (initial baseline and reset target)
DEFAULT_RATE_LIMITS: dict[str, int] = {
    "submit_rate_limit_hour": 500,
    "submit_rate_limit_day": 2000,
    "secure_submit_rate_limit_hour": 500,
    "secure_submit_rate_limit_day": 2000,
    "assessment_session_limit_hour": 3,
    "invalid_token_limit_minute": 10,
}

# Validation constraints
RATE_LIMIT_CONSTRAINTS: dict[str, dict[str, Any]] = {
    "submit_rate_limit_hour": {"min": 1, "max": 100_000, "label": "Public submissions per IP per hour"},
    "submit_rate_limit_day": {"min": 1, "max": 1_000_000, "label": "Public submissions per IP per day"},
    "secure_submit_rate_limit_hour": {"min": 1, "max": 100_000, "label": "Secure-link submissions per IP per hour"},
    "secure_submit_rate_limit_day": {"min": 1, "max": 1_000_000, "label": "Secure-link submissions per IP per day"},
    "assessment_session_limit_hour": {"min": 1, "max": 100, "label": "Assessment session attempts per hour"},
    "invalid_token_limit_minute": {"min": 1, "max": 1_000, "label": "Invalid-token attempts per IP per minute"},
}

# In-memory synchronization lock & snapshot
_lock = threading.RLock()
_cached_settings: dict[str, int] = {}
_cached_descriptions: dict[str, str] = {}
_last_updated_at: Optional[str] = None
_last_updated_by: str = "system"
_last_sync_timestamp: float = 0.0

# Cross-worker invalidation file
INVALIDATION_FILE = Path(os.environ.get("NIWI_RATE_LIMIT_INVALIDATION_FILE", "/tmp/niwi_rate_limit_version"))
_last_mtime_ns: int = 0

# Runtime metrics
_429_count: int = 0
_last_429_at: Optional[str] = None


def get_client_ip(request: Request) -> str:
    """
    Extracts the authentic client IP address behind trusted Nginx proxy.
    Prefers X-Real-IP set directly by local Nginx proxy.
    """
    if not request:
        return "127.0.0.1"

    # Priority 1: X-Real-IP directly configured in Nginx
    real_ip = request.headers.get("x-real-ip")
    if real_ip and real_ip.strip():
        return real_ip.strip()

    # Priority 2: Leftmost IP from X-Forwarded-For
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        if parts:
            return parts[0]

    # Fallback: direct connection host
    if hasattr(request, "client") and request.client and request.client.host:
        return request.client.host

    return "127.0.0.1"


def _get_env_fallback(key: str, default_val: int) -> int:
    """Retrieves environment variable fallback if set, otherwise default_val."""
    env_var_name = key.upper()
    val_str = os.environ.get(env_var_name)
    if val_str:
        try:
            return int(val_str.strip())
        except ValueError:
            pass
    return default_val


def _load_settings_from_db() -> tuple[dict[str, int], dict[str, str], Optional[str], str]:
    """Loads active rate-limit configuration directly from PostgreSQL."""
    settings = {}
    descriptions = {}
    latest_updated_at = None
    latest_updated_by = "system"

    # Pre-populate defaults with environment variable hierarchy
    for k, v in DEFAULT_RATE_LIMITS.items():
        settings[k] = _get_env_fallback(k, v)
        descriptions[k] = RATE_LIMIT_CONSTRAINTS[k]["label"]

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                cur.execute("""
                    SELECT setting_key, setting_value, description, updated_at, updated_by
                    FROM system_security_settings
                """)
                rows = cur.fetchall()
                for r in rows:
                    key = r["setting_key"]
                    val_str = r["setting_value"]
                    if key in DEFAULT_RATE_LIMITS:
                        try:
                            settings[key] = int(val_str)
                            descriptions[key] = r["description"] or descriptions.get(key, "")
                            if r["updated_at"]:
                                dt_iso = r["updated_at"].isoformat()
                                if not latest_updated_at or dt_iso > latest_updated_at:
                                    latest_updated_at = dt_iso
                                    latest_updated_by = r["updated_by"] or "admin"
                        except (ValueError, TypeError):
                            logger.warning("Invalid value for %s in DB: %s, using fallback", key, val_str)
    except Exception as e:
        logger.error("Failed to load system_security_settings from database: %s", e)

    return settings, descriptions, latest_updated_at, latest_updated_by


def _check_and_sync():
    """Checks if invalidation file has been touched or cache is empty and reloads if needed."""
    global _cached_settings, _cached_descriptions, _last_updated_at, _last_updated_by
    global _last_mtime_ns, _last_sync_timestamp

    needs_reload = False
    current_time = time.time()

    if not _cached_settings:
        needs_reload = True
    elif INVALIDATION_FILE.exists():
        try:
            mtime = INVALIDATION_FILE.stat().st_mtime_ns
            if mtime != _last_mtime_ns:
                needs_reload = True
        except OSError:
            pass

    if needs_reload:
        with _lock:
            settings, descriptions, updated_at, updated_by = _load_settings_from_db()
            _cached_settings = settings
            _cached_descriptions = descriptions
            _last_updated_at = updated_at
            _last_updated_by = updated_by
            _last_sync_timestamp = current_time
            if INVALIDATION_FILE.exists():
                try:
                    _last_mtime_ns = INVALIDATION_FILE.stat().st_mtime_ns
                except OSError:
                    pass
            logger.info("Rate limit settings refreshed from PostgreSQL: %s", _cached_settings)


def notify_workers():
    """Touches the invalidation file so all Uvicorn worker processes refresh their cache."""
    try:
        INVALIDATION_FILE.parent.mkdir(parents=True, exist_ok=True)
        now_ts = str(time.time_ns())
        INVALIDATION_FILE.write_text(now_ts)
    except Exception as e:
        logger.warning("Failed to touch rate limit invalidation file: %s", e)


def get_current_limits() -> dict[str, int]:
    """Returns active rate-limit dictionary for high-speed runtime lookups."""
    _check_and_sync()
    with _lock:
        return dict(_cached_settings)


def get_rate_limit_config_response() -> dict[str, Any]:
    """Returns complete settings payload for Admin UI & API."""
    _check_and_sync()
    with _lock:
        settings = dict(_cached_settings)
        descriptions = dict(_cached_descriptions)
        updated_at = _last_updated_at
        updated_by = _last_updated_by
        sync_ts = _last_sync_timestamp
        count_429 = _429_count
        last_429 = _last_429_at

    return {
        "settings": settings,
        "defaults": DEFAULT_RATE_LIMITS,
        "descriptions": descriptions,
        "constraints": RATE_LIMIT_CONSTRAINTS,
        "last_updated_at": updated_at,
        "last_updated_by": updated_by,
        "last_synced_at": datetime.fromtimestamp(sync_ts, tz=timezone.utc).isoformat() if sync_ts else None,
        "sync_status": "SYNCHRONIZED",
        "metrics": {
            "rate_limit_exceeded_total": count_429,
            "last_rate_limit_exceeded_at": last_429,
            "active_mode": "POSTGRESQL_DYNAMIC",
        }
    }


def validate_rate_limit_values(values: dict[str, Any]) -> dict[str, int]:
    """Validates submitted rate-limit values against schema and logic rules."""
    cleaned = {}
    for key, rule in RATE_LIMIT_CONSTRAINTS.items():
        if key not in values:
            raise ValueError(f"Missing required rate limit setting: '{key}'")
        raw_val = values[key]

        # Reject floats, booleans, strings that aren't clean ints
        if isinstance(raw_val, (bool, float)) or raw_val is None:
            raise ValueError(f"Setting '{key}' must be an integer.")
        try:
            val = int(raw_val)
        except (ValueError, TypeError):
            raise ValueError(f"Setting '{key}' must be a valid integer, got '{raw_val}'.")

        if val < rule["min"]:
            raise ValueError(f"Setting '{key}' cannot be less than {rule['min']}.")
        if val > rule["max"]:
            raise ValueError(f"Setting '{key}' cannot exceed {rule['max']:,}.")

        cleaned[key] = val

    # Logical validation: daily must be >= hourly
    if cleaned["submit_rate_limit_day"] < cleaned["submit_rate_limit_hour"]:
        raise ValueError("Public daily limit cannot be less than hourly limit.")
    if cleaned["secure_submit_rate_limit_day"] < cleaned["secure_submit_rate_limit_hour"]:
        raise ValueError("Secure-link daily limit cannot be less than hourly limit.")

    return cleaned


def update_rate_limit_settings(new_values: dict[str, Any], admin_email: str, client_ip: str) -> dict[str, Any]:
    """
    Validates, persists, logs, and synchronizes updated rate limit settings.
    """
    cleaned = validate_rate_limit_values(new_values)
    current = get_current_limits()

    now = datetime.now(timezone.utc)
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                for k, v in cleaned.items():
                    cur.execute("""
                        INSERT INTO system_security_settings (setting_key, setting_value, updated_at, updated_by)
                        VALUES (%s, %s, %s, %s)
                        ON CONFLICT (setting_key) DO UPDATE
                        SET setting_value = EXCLUDED.setting_value,
                            updated_at = EXCLUDED.updated_at,
                            updated_by = EXCLUDED.updated_by
                    """, (k, str(v), now, admin_email))

                # Record audit log
                cur.execute("""
                    INSERT INTO audit_logs (admin_id, action_type, old_value, new_value, ip_address)
                    VALUES (%s, %s, %s, %s, %s)
                """, (
                    admin_email,
                    "update_rate_limits",
                    json.dumps(current),
                    json.dumps(cleaned),
                    client_ip,
                ))

    # Update local in-memory cache immediately in current process
    with _lock:
        _cached_settings = dict(cleaned)
        _last_updated_at = now.isoformat()
        _last_updated_by = admin_email
        _last_sync_timestamp = time.time()

    # Touch invalidation file so peer workers reload
    notify_workers()
    if INVALIDATION_FILE.exists():
        try:
            _last_mtime_ns = INVALIDATION_FILE.stat().st_mtime_ns
        except OSError:
            pass

    logger.info("Admin %s updated rate limits from %s: %s", admin_email, client_ip, cleaned)
    return get_rate_limit_config_response()


def reset_rate_limit_settings(admin_email: str, client_ip: str) -> dict[str, Any]:
    """Restores system default rate-limit settings."""
    return update_rate_limit_settings(DEFAULT_RATE_LIMITS, admin_email, client_ip)


# ---------------------------------------------------------------------------
# Dynamic SlowAPI Limit Callables
# ---------------------------------------------------------------------------

def get_public_submit_hourly_limit() -> str:
    limits = get_current_limits()
    return f"{limits['submit_rate_limit_hour']}/hour"


def get_public_submit_daily_limit() -> str:
    limits = get_current_limits()
    return f"{limits['submit_rate_limit_day']}/day"


def get_secure_submit_hourly_limit() -> str:
    limits = get_current_limits()
    return f"{limits['secure_submit_rate_limit_hour']}/hour"


def get_secure_submit_daily_limit() -> str:
    limits = get_current_limits()
    return f"{limits['secure_submit_rate_limit_day']}/day"


def get_session_hourly_limit() -> str:
    limits = get_current_limits()
    return f"{limits['assessment_session_limit_hour']}/hour"


def get_invalid_token_minute_limit() -> str:
    limits = get_current_limits()
    return f"{limits['invalid_token_limit_minute']}/minute"


def get_effective_submit_hourly_limit() -> str:
    """Returns upper-bound hourly limit across public and secure channels for outer SlowAPI guard."""
    limits = get_current_limits()
    max_hr = max(limits["submit_rate_limit_hour"], limits["secure_submit_rate_limit_hour"])
    return f"{max_hr}/hour"


def get_effective_submit_daily_limit() -> str:
    """Returns upper-bound daily limit across public and secure channels for outer SlowAPI guard."""
    limits = get_current_limits()
    max_day = max(limits["submit_rate_limit_day"], limits["secure_submit_rate_limit_day"])
    return f"{max_day}/day"


# ---------------------------------------------------------------------------
# Dynamic Traffic Classification & Enforcement
# ---------------------------------------------------------------------------

def record_rate_limit_exceeded(key: str, limit_str: str, client_ip: str, classification: str):
    """Tracks metrics and sets state on rate limit violation."""
    global _429_count, _last_429_at
    with _lock:
        _429_count += 1
        _last_429_at = datetime.now(timezone.utc).isoformat()
    logger.warning(
        "Rate limit exceeded: classification=%s, ip=%s, key=%s, limit=%s (total_429=%d)",
        classification, client_ip, key, limit_str, _429_count
    )


def _raise_rate_limit_exceeded(request: Request, limit_str: str, key: str, client_ip: str, classification: str):
    """Constructs and raises RateLimitExceeded compatible with SlowAPI exception handler."""
    record_rate_limit_exceeded(key, limit_str, client_ip, classification)
    limit_item = parse(limit_str)
    # SlowAPI's exception handler reads request.state.view_rate_limit
    request.state.view_rate_limit = str(limit_item)
    limit_obj = Limit(
        limit_item,
        lambda r: key,
        None,
        False,
        None,
        limit_str,
        None,
        1,
        True,
    )
    raise RateLimitExceeded(limit_obj)


def enforce_submission_rate_limits(request: Request, data: dict[str, Any]):
    """
    Evaluates submission payload and client context to dynamically enforce:
      - Policy A: Public submissions per-IP hourly & daily limits.
      - Policy B: Valid secure-link submissions per-IP hourly & daily limits.
      - Policy C: Assessment session attempt bounds (server-issued draft IDs).
      - Policy D: Invalid / revoked assessment token abuse protection.
    """
    client_ip = get_client_ip(request)
    limits = get_current_limits
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `app/services/scoring_service.py`

```python
"""
scoring.py — NeuroMark Audit scoring logic
"""

import html as html_module
import logging

logger = logging.getLogger(__name__)
import math
import json
import os
import urllib.parse
from datetime import datetime, timezone, timedelta
import psycopg2.extras

from app.services.settings_service import get_settings

IST = timezone(timedelta(hours=5, minutes=30))

DIMENSION_COMMENTARY = {
    "lc": {
        "low": "Your leadership has yet to prioritize neuro-inclusion. Initiating sponsor education and drafting basic DEI policy statements is highly recommended.",
        "med": "Early culture changes are visible under committed leaders. Establish structured metrics and encourage senior sponsors to serve as public role models.",
        "high": "Inclusion is deeply embedded in your culture and values. Maintain this maturity by scaling audit tracking and mentoring other sector peers."
    },
    "ro": {
        "low": "Job design and recruitment screening pose major neurodivergent barriers. Standardize basic interview adjustments and share questions in advance.",
        "med": "Hiring processes offer minor flexibilities but need consistency. Train recruitment staff on neuroinclusive interview models.",
        "high": "Highly tailored talent acquisition pipelines attract diverse profiles. Scale strengths-based hiring strategies across all business units."
    },
    "we": {
        "low": "Employees face high hurdles securing work adjustments. Formalize request frameworks and equip managers to handle cases without bias.",
        "med": "Reasonable adjustments are available but inconsistently applied. Focus on manager capability training and feedback capture.",
        "high": "Flexible adjustments are fully normalized and proactive. Regularly audit tool options and adjust processes to secure productivity."
    },
    "be": {
        "low": "Your physical space induces significant sensory load. Conduct workspace sensory audits and establish a designated quiet zone.",
        "med": "Some quiet corners and adjustable lights exist. Introduce structured wayfinding and sensory training for space planners.",
        "high": "Sensory accessibility guides all office space decisions. Maintain active feedback networks with neurodivergent employees."
    },
    "tm": {
        "low": "Appraisal patterns heavily restrict neurodivergent career paths. Standardize strengths-based review targets for all departments.",
        "med": "Performance metrics are flexible but lack developmental backing. Introduce structured mentorship programs.",
        "high": "Promotions and careers center around individual team strengths. Regularly track retention data to secure equal growth opportunity."
    },
    "ca": {
        "low": "Corporate messaging is filled with complex jargon. Mandate plain language standards and multi-format communications.",
        "med": "Some emails use simple layouts, but agendas are rarely shared. Ensure digital tools are tested for user accessibility.",
        "high": "All channels strictly employ clear, accessible communications. Keep reviewing new software tools against accessibility guidelines."
    },
    "pc": {
        "low": "Client channels create accessibility friction. Initiate co-design sessions to remove sensory or navigation difficulties.",
        "med": "Minor digital adaptations have resolved simple user issues. Focus on customer service training to handle customer adjustments.",
        "high": "Products are designed with complete neuroinclusive focus. Maintain this standard by engaging active product testing groups."
    },
    "sp": {
        "low": "Supplier choices fail to capture DEI alignments. Insert simple neurodiversity commitment criteria in your standard RFP process.",
        "med": "Supplier reviews show early neuroinclusive trends. Formally integrate these audits in vendor review meetings.",
        "high": "Your supply chain amplifies strong neuroinclusive practices. Highlight these supplier partnerships to set sector examples."
    }
}

def get_maturity_level(score: int) -> str:
    if score <= 6:
        return "Level 1 — Foundational"
    elif score <= 14:
        return "Level 2 — Early Progress"
    else:
        return "Level 3 — Developing"

OVERALL_SYNOPSIS = [
    "Your organisation is at the start of its neuro-inclusion journey. "
    "There is significant opportunity to build awareness, remove barriers, and create a more inclusive environment. "
    "We recommend beginning with leadership education and a structured inclusion plan. "
    "Orchvate is here to support you every step of the way.",

    "Your organisation has made meaningful early progress on neuro-inclusion. "
    "There are pockets of good practice, but consistency and embedding are the next steps. "
    "With focused effort across the key areas, you can build a genuinely inclusive culture. "
    "Orchvate can help you prioritise and accelerate your progress.",

    "Your organisation is developing a strong foundation for neuro-inclusion. "
    "You are ahead of many organisations and have much to be proud of. "
    "The focus now is on embedding, measuring impact, and continuing to improve. "
    "Orchvate can support you in reaching and sustaining best practice.",
]

def score_section(data: dict, section_key: str, questions: list) -> tuple[float, int, int]:
    n_total = len(questions)
    # Exclude questions answered with NA
    applicable_questions = [q for q in questions if data.get(q["field_name"], "") not in ("NA", "N/A")]
    n_applicable = len(applicable_questions)

    if n_applicable == 0:
        return 0, 0, 0

    raw_score = 0
    max_applicable = 0
    max_total = 0
    not_sure_count = 0

    for q in questions:
        # Determine max score for this question based on its score_mapping
        q_max = max(q["score_mapping"].values()) if q["score_mapping"] else 4
        max_total += q_max

        ans = data.get(q["field_name"], "")
        if ans not in ("NA", "N/A"):
            if ans == "Not Sure":
                not_sure_count += 1
            raw_score += q["score_mapping"].get(ans, 0)
            max_applicable += q_max

    if n_applicable == n_total:
        return raw_score, not_sure_count, n_applicable

    if max_applicable == 0:
        return 0, not_sure_count, n_applicable

    # Rescale
    return round((raw_score / max_applicable) * max_total, 2), not_sure_count, n_applicable


DEFAULT_STANDARD_SECTIONS = [
    {"section": {"section_code": "lc", "title": "Leadership & Culture", "gating_field": None},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(5, 10)]},
    {"section": {"section_code": "ro", "title": "Recruitment & Onboarding", "gating_field": None},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(10, 15)]},
    {"section": {"section_code": "we", "title": "Work Environment", "gating_field": None},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(15, 20)]},
    {"section": {"section_code": "be", "title": "Built Environment", "gating_field": "has_physical_workspace"},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(20, 25)]},
    {"section": {"section_code": "tm", "title": "Talent Management", "gating_field": None},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(25, 30)]},
    {"section": {"section_code": "ca", "title": "Communication & Accessibility", "gating_field": None},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(30, 35)]},
    {"section": {"section_code": "pc", "title": "Products & Customer Service", "gating_field": None},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(35, 40)]},
    {"section": {"section_code": "sp", "title": "Supply Chain & Procurement", "gating_field": "has_suppliers"},
     "questions": [{"field_name": f"q{i}", "score_mapping": {"Yes": 4, "Partially": 2, "No": 0, "Not Sure": 0}} for i in range(40, 45)]},
]

import time
import threading

_cached_form_sections = None
_cached_form_sections_time = 0.0
_cache_lock = threading.Lock()
_SECTIONS_CACHE_TTL = 300.0  # 5 minutes


def get_form_sections_metadata(conn=None) -> tuple[list, int]:
    """
    Retrieve form sections and threshold with TTL caching and stale-while-revalidate protection.
    Uses a single SQL query with LEFT JOIN and json_agg to eliminate N+1 round trips.
    If called with conn=None when cache expires, borrows a pooled DB connection.
    If DB is temporarily unreachable, retains existing cached sections rather than
    downgrading to default standard questions.
    """
    global _cached_form_sections, _cached_form_sections_time
    now = time.time()
    if _cached_form_sections is not None and (now - _cached_form_sections_time) < _SECTIONS_CACHE_TTL:
        return _cached_form_sections

    with _cache_lock:
        # Double-check inside lock
        now = time.time()
        if _cached_form_sections is not None and (now - _cached_form_sections_time) < _SECTIONS_CACHE_TTL:
            return _cached_form_sections

        threshold = 50
        sections = []
        owned_conn = None
        active_conn = conn

        if active_conn is None:
            try:
                from app.core.database import get_conn
                owned_conn = get_conn()
                active_conn = owned_conn
            except Exception as conn_err:
                logger.warning("Could not borrow connection for form metadata refresh: %s", conn_err)
                active_conn = None

        if active_conn is not None:
            try:
                with active_conn.cursor() as cur:
                    cur.execute("""
                        SELECT 
                            s.id, s.section_code, s.title, s.icon, s.summary, s.why_it_matters, s.tip, 
                            s.gating_question, s.gating_field, s.order_index,
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
                            ) AS questions,
                            COALESCE((SELECT low_visibility_threshold FROM app_settings WHERE id = 1), 50) AS threshold
                        FROM form_sections s
                        LEFT JOIN form_questions q ON s.id = q.section_id
                        GROUP BY s.id
                        ORDER BY s.order_index ASC;
                    """)
                    rows = cur.fetchall()
                    for r in rows:
                        sec_dict = {
                            "id": r[0], "section_code": r[1], "title": r[2], "icon": r[3],
                            "summary": r[4], "why_it_matters": r[5], "tip": r[6],
                            "gating_question": r[7], "gating_field": r[8], "order_index": r[9]
                        }
                        q_data = r[10] if isinstance(r[10], list) else json.loads(r[10])
                        sections.append({"section": sec_dict, "questions": q_data})
                        threshold = int(r[11]) if r[11] is not None else 50
            except Exception as fetch_err:
                logger.warning("Error fetching form sections from database: %s", fetch_err)
                sections = []
            finally:
                if owned_conn is not None:
                    try:
                        owned_conn.close()
                    except Exception:
                        pass

        # Stale-while-revalidate protection:
        if not sections:
            if _cached_form_sections is not None:
                logger.warning("DB query yielded no sections; retaining previously cached form sections")
                return _cached_form_sections
            sections = DEFAULT_STANDARD_SECTIONS

        _cached_form_sections = (sections, threshold)
        _cached_form_sections_time = now
        return _cached_form_sections


def calculate_scores_pure(data: dict, sections: list = None, threshold: int = 50) -> dict:
    """
    Pure, deterministic scoring engine (CALC-001 through CALC-006).
    Performs zero database queries and zero network operations.
    """
    if not sections:
        sections = DEFAULT_STANDARD_SECTIONS

    result = {}
    section_scores = []
    dimension_scores = {}
    low_visibility_sections = []

    for s_info in sections:
        sec = s_info["section"]
        qs = s_info["questions"]
        key = sec["section_code"]
        label = sec["title"]

        # Check gating
        gating_field = sec.get("gating_field")
        if gating_field and data.get(gating_field) == "No":
            result[f"{key}_score"] = "NA"
            result[f"{key}_level"] = "Not applicable"
            dimension_scores[key] = "NA"
            section_scores.append((key, label, "NA", "Not applicable", False))
            continue

        score, not_sure_count, n_applicable = score_section(data, key, qs)
        level = get_maturity_level(score)

        is_low_visibility = False
        if n_applicable > 0 and not_sure_count >= (n_applicable * threshold / 100.0):
            is_low_visibility = True
            low_visibility_sections.append(key)

        result[f"{key}_score"] = score
        result[f"{key}_level"] = level
        dimension_scores[key] = score
        section_scores.append((key, label, score, level, is_low_visibility))

    valid_scores = [s[2] for s in section_scores if s[2] != "NA"]
    overall_avg = round(sum(valid_scores) / len(valid_scores), 2) if valid_scores else 0
    overall_level = get_maturity_level(int(overall_avg))
    result["overall_avg"] = overall_avg
    result["overall_level"] = overall_level
    result["dimension_scores"] = dimension_scores
    result["low_visibility_sections"] = low_visibility_sections
    result["_section_scores"] = section_scores
    return result


def calculate_scores(data: dict, conn=None) -> dict:
    """
    Main scoring function. Preserves backwards-compatibility by compiling
    email_body on demand for legacy callers.
    """
    sections, threshold = get_form_sections_metadata(conn)
    result = calculate_scores_pure(data, sections=sections, threshold=threshold)

    result["email_body"] = build_email(
        name=data.get("name", ""),
        designation=data.get("designation", "") or data.get("role", ""),
        company_name=data.get("company_name", ""),
        contact_number=data.get("contact_number", ""),
        section_scores=result.get("_section_scores", [])
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `app/services/settings_service.py`

```python
"""
Settings and admin notification emails.
"""

import html as html_module
import logging
import os
import threading
import time
from typing import Tuple, Optional

from azure.communication.email import EmailClient

logger = logging.getLogger(__name__)

DEFAULT_SUPPORT_EMAIL = "aakash.padyachi@rochvate.com"

_settings_cache: Optional[dict] = None
_settings_cache_time: float = 0.0
_settings_lock = threading.Lock()
_SETTINGS_CACHE_TTL = 60.0  # 60 seconds


def _env_sender():
    return {
        "sender_name": os.environ.get("ACS_SENDER_NAME", "Orchvate"),
        "sender_address": os.environ.get("ACS_SENDER_ADDRESS", ""),
    }


_app_settings_table_exists = None


def ensure_settings_table(cur):
    global _app_settings_table_exists
    if _app_settings_table_exists is True:
        return

    try:
        cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE  table_schema = 'public'
                AND    table_name   = 'app_settings'
            )
            """
        )
        exists = cur.fetchone()[0]
        if not exists:
            logger.info("Creating missing app_settings table...")
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS app_settings (
                    id                      INT PRIMARY KEY DEFAULT 1 CHECK (id = 1),
                    sender_name             VARCHAR(255) NOT NULL DEFAULT 'Orchvate',
                    sender_address          VARCHAR(255) NOT NULL DEFAULT '',
                    notification_email      TEXT NOT NULL DEFAULT '',
                    notification_cc_email   TEXT NOT NULL DEFAULT '',
                    notifications_enabled   BOOLEAN NOT NULL DEFAULT FALSE,
                    support_email           VARCHAR(255) NOT NULL DEFAULT 'aakash.padyachi@rochvate.com',
                    crm_sync_enabled        BOOLEAN NOT NULL DEFAULT FALSE,
                    hubspot_api_key         TEXT NOT NULL DEFAULT '',
                    low_visibility_threshold INT NOT NULL DEFAULT 50,
                    updated_at              TIMESTAMP DEFAULT NOW()
                );
                """
            )
            
        # Ensure columns exist for older installations
        cur.execute(
            """
            ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS crm_sync_enabled BOOLEAN NOT NULL DEFAULT FALSE;
            ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS hubspot_api_key TEXT NOT NULL DEFAULT '';
            ALTER TABLE app_settings ADD COLUMN IF NOT EXISTS low_visibility_threshold INT NOT NULL DEFAULT 50;
            """
        )
        _app_settings_table_exists = True
    except Exception as e:
        logger.warning("Error ensuring app_settings table: %s", e)

def ensure_settings_row(cur):
    ensure_settings_table(cur)
    env = _env_sender()
    try:
        cur.execute(
            """
            INSERT INTO app_settings (
                id, sender_name, sender_address, notification_email, notification_cc_email, notifications_enabled, support_email
            )
            VALUES (1, %s, %s, '', '', FALSE, 'aakash.padyachi@rochvate.com')
            ON CONFLICT (id) DO NOTHING
            """,
            (env["sender_name"], env["sender_address"]),
        )
    except Exception as e:
        logger.warning("Error ensuring settings row: %s", e)


def get_settings(cur=None) -> dict:
    global _settings_cache, _settings_cache_time
    now = time.time()
    if _settings_cache is not None and (now - _settings_cache_time) < _SETTINGS_CACHE_TTL:
        return _settings_cache

    with _settings_lock:
        now = time.time()
        if _settings_cache is not None and (now - _settings_cache_time) < _SETTINGS_CACHE_TTL:
            return _settings_cache

        def _fetch(cursor):
            cursor.execute(
                """
                SELECT sender_name, sender_address, notification_email, notification_cc_email,
                       notifications_enabled, support_email, updated_at, crm_sync_enabled, hubspot_api_key,
                       low_visibility_threshold
                FROM app_settings WHERE id = 1
                """
            )
            return cursor.fetchone()

        row = None
        if cur is not None:
            try:
                row = _fetch(cur)
            except Exception:
                ensure_settings_row(cur)
                row = _fetch(cur)
        else:
            from app.core.database import get_db_connection
            with get_db_connection() as conn:
                with conn.cursor() as c:
                    try:
                        row = _fetch(c)
                    except Exception:
                        ensure_settings_row(c)
                        row = _fetch(c)

        if not row and cur is not None:
            ensure_settings_row(cur)
            row = _fetch(cur)

        if not row:
            env = _env_sender()
            _settings_cache = {
                "sender_name": env["sender_name"],
                "sender_address": env["sender_address"],
                "notification_email": "",
                "notification_cc_email": "",
                "notifications_enabled": False,
                "support_email": DEFAULT_SUPPORT_EMAIL,
                "updated_at": None,
                "crm_sync_enabled": False,
                "hubspot_api_key": "",
                "low_visibility_threshold": 50
            }
            _settings_cache_time = now
            return _settings_cache

        _settings_cache = {
            "sender_name": row[0] or _env_sender()["sender_name"],
            "sender_address": row[1] or _env_sender()["sender_address"],
            "notification_email": row[2] or "",
            "notification_cc_email": row[3] or "",
            "notifications_enabled": bool(row[4]),
            "support_email": (row[5] or "").strip() or DEFAULT_SUPPORT_EMAIL,
            "updated_at": row[6].isoformat() if row[6] else None,
            "crm_sync_enabled": bool(row[7]),
            "hubspot_api_key": row[8] or "",
            "low_visibility_threshold": int(row[9]) if row[9] is not None else 50
        }
        _settings_cache_time = now
        return _settings_cache


def update_settings(cur, data: dict) -> dict:
    global _settings_cache, _settings_cache_time
    with _settings_lock:
        _settings_cache = None
        _settings_cache_time = 0.0

    ensure_settings_row(cur)
    current = get_settings(cur)

    sender_name = (data.get("sender_name") if "sender_name" in data else current["sender_name"]) or "Orchvate"
    sender_address = (
        data.get("sender_address") if "sender_address" in data else current["sender_address"]
    ) or _env_sender()["sender_address"]
    notification_email = (
        data.get("notification_email") if "notification_email" in data else current["notification_email"]
    ) or ""
    notification_cc_email = (
        data.get("notification_cc_email") if "notification_cc_email" in data else current["notification_cc_email"]
    ) or ""
    notifications_enabled = (
        data["notifications_enabled"]
        if "notifications_enabled" in data
        else current["notifications_enabled"]
    )
    support_email = (
        data.get("support_email") if "support_email" in data else current["support_email"]
    ) or DEFAULT_SUPPORT_EMAIL
    crm_sync_enabled = (
        data["crm_sync_enabled"]
        if "crm_sync_enabled" in data
        else current["crm_sync_enabled"]
    )
    hubspot_api_key = (
        data.get("hubspot_api_key") if "hubspot_api_key" in data else current["hubspot_api_key"]
    ) or ""
    low_visibility_threshold = (
        int(data.get("low_visibility_threshold")) if "low_visibility_threshold" in data else current["low_visibility_threshold"]
    )

    cur.execute(
        """
        UPDATE app_settings SET
            sender_name = %s,
            sender_address = %s,
            notification_email = %s,
            notification_cc_email = %s,
            notifications_enabled = %s,
            support_email = %s,
            crm_sync_enabled = %s,
            hubspot_api_key = %s,
            low_visibility_threshold = %s,
            updated_at = NOW()
        WHERE id = 1
        """,
        (sender_name, sender_address, notification_email, notification_cc_email, notifications_enabled, support_email, crm_sync_enabled, hubspot_api_key, low_visibility_threshold),
    )
    return get_settings(cur)


def get_sender_for_send(cur) -> Tuple[str, str]:
    settings = get_settings(cur)
    env = _env_sender()
    address = settings["sender_address"] or env["sender_address"]
    name = settings["sender_name"] or env["sender_name"]
    return address, name


def is_acs_configured() -> bool:
    """Check if Azure Communication Services is configured."""
    acs_conn = os.environ.get("ACS_CONNECTION_STRING") or os.environ.get("ACS-CONNECTION-STRING", "")
    return bool(acs_conn and acs_conn.strip())


def send_acs_email(*, to_addresses: list[str] = None, to_address: str = None, to_name: str = "", cc_addresses: list[str] = None, subject: str, html: str, plain: str,
                   sender_address: str, sender_name: str, submission_id: str = None) -> bool:
    """
    Send email via Azure Communication Services.
    Returns True if successfully submitted to ACS.
    Returns False if ACS is intentionally not configured.
    Raises exception on external send failure.
    """
    if not is_acs_configured():
        logger.warning("ACS_CONNECTION_STRING not configured. Email dispatch bypassed for submission %s", submission_id)
        return False
    acs_conn = os.environ.get("ACS_CONNECTION_STRING") or os.environ.get("ACS-CONNECTION-STRING", "")
    client = EmailClient.from_connection_string(acs_conn)
    
    to_recipients = [{"address": a.strip()} for a in to_addresses if a.strip()] if to_addresses else [{"address": to_address, "displayName": to_name}]
    message = {
        "senderAddress": sender_address,
        "recipients": {"to": to_recipients},
        "content": {"subject": subject, "html": html, "plainText": plain},
        "replyTo": [{"address": sender_address, "displayName": sender_name}],
        "headers": {
            "X-Priority": "3",
            "Importance": "normal",
            "X-Mailer": "NeuroMark Audit System",
        }
    }
    
    # Add submission tracking header if provided
    if submission_id:
        message["headers"]["X-Entity-Ref-ID"] = f"submission-{submission_id}"
    
    if cc_addresses:
        cc_recipients = [{"address": c.strip()} for c in cc_addresses if c.strip()]
        if cc_recipients:
            message["recipients"]["cc"] = cc_recipients

    poller = client.begin_send(message)
    poller.result()
    logger.info("ACS email successfully accepted by provider for submission %s", submission_id)
    return True


def notify_admin_new_submission(cur, submission_id: int, name: str, company_name: str, sync: bool = False):
    """
    Send admin alert if notifications are enabled.
    When sync=True: runs synchronously and returns (status, error_or_message).
    When sync=False: runs in background thread and returns bool (for backward compatibility).
    """
    settings = get_settings(cur)
    
    if not settings["notifications_enabled"]:
        logger.info(f"Notifications disabled - skipping admin alert for submission {submission_id}")
        return ("SKIPPED", "Notifications disabled") if sync else False
        
    admin_emails = [e.strip() for e in (settings["notification_email"] or "").replace(";", ",").split(",") if e.strip()]
    if not admin_emails:
        logger.warning(f"Notifications enabled but notification_email is empty for submission {submission_id}")
        return ("SKIPPED", "No notification email configured") if sync else False
        
    cc_emails = [e.strip() for e in (settings.get("notification_cc_email") or "").replace(";", ",").split(",") if e.strip()]

    sender_address, sender_name = get_sender_for_send(cur)
    if not sender_address:
        logger.error(f"No sender address configured for admin notification (submission {submission_id})")
        return ("SKIPPED", "No sender address configured") if sync else False

    if not is_acs_configured():
        logger.info(f"ACS_CONNECTION_STRING not configured - skipping admin notification for submission {submission_id}")
        return ("SKIPPED", "ACS not configured") if sync else False

    frontend_base = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    review_url = f"{frontend_base}/admin/submissions/{submission_id}"

    subject = f"New audit to review — {company_name}"
    plain = (
        f"A new NeuroMark Audit has been submitted.\n\n"
        f"Organisation: {company_name}\n"
        f"Respondent: {name}\n"
        f"Submission ID: {submission_id}\n\n"
        f"Review the submission: {review_url}\n"
    )
    html = (
        f"<p>A new <strong>NeuroMark Audit</strong> has been submitted and is ready for your review.</p>"
        f"<p><strong>Organisation:</strong> {company_name}<br>"
        f"<strong>Respondent:</strong> {name}<br>"
        f"<strong>Submission ID:</strong> {submission_id}</p>"
        f'<p><a href="{review_url}" style="display:inline-block;background:#1E1A4A;color:#FFFFFF;padding:10px 20px;border-radius:6px;text-decoration:none;font-weight:600;">Open Submission →</a></p>'
    )

    if sync:
        try:
            logger.info(f"Synchronously sending admin notification for submission {submission_id} to {', '.join(admin_emails)}")
            send_acs_email(
                to_addresses=admin_emails,
                cc_addresses=cc_emails if cc_emails else None,
                subject=subject,
                html=html,
                plain=plain,
                sender_address=sender_address,
                sender_name=sender_name,
                submission_id=str(submission_id),
            )
            return ("SENT", None)
        except Exception as e:
            logger.error(f"Synchronous admin notification failed for submission {submission_id}: {e}")
            raise

    try:
        import threading
        
        logger.info(f"Attempting to send admin notification for submission {submission_id} to {', '.join(admin_emails)}")
        
        def bg_send():
            try:
                send_acs_email(
                    to_addresses=admin_emails,
                    cc_addresses=cc_emails if cc_emails else None,
                    subject=subject,
                    html=html,
                    plain=plain,
                    sender_address=sender_address,
                    sender_name=sender_name,
                    submission_id=str(submission_id),
                )
                logger.info(f"Admin notification sent successfully for submission {submission_id}")
            except Exception as e:
                logger.error(f"Background admin notification failed for submission {submission_id}: {e}")
                import traceback
                logger.error(traceback.format_exc())
                
        threading.Thread(target=bg_send, daemon=True).start()
        return True
    except Exception as e:
        logger.error(f"Failed to start admin notification thread for submission {submission_id}: {e}")
        return False


def get_support_email(cur) -> str:
    settings = get_settings(cur)
    return (
        (settings.get("support_email") or "").strip()
        or os.environ.get("SUPPORT_EMAIL", "").strip()
        or DEFAULT_SUPPORT_EMAIL
    )


def send_support_request(cur, name: str, email: str, subject: str, message: str) -> None:
    """Email support inbox when a user submits the support form."""
    to_address = get_support_email(cur)
    sender_address, sender_name = get_sender_for_send(cur)
    if not sender_address:
        raise ValueError("Sender address is not configured")

    def esc(t):
        r
```
> _Truncated to 16000 bytes — see full file in the source repo._

#### `app/services/token_service.py`

```python
"""
token_service.py — Secure Assessment Access Token Service
Generates cryptographically random 256-bit access tokens, stores SHA-256 hashes,
and resolves assessment links securely without exposing organisation identifiers in URLs.
Provides backward compatibility for existing organization invitations.
"""

import base64
import hashlib
import json
import logging
import secrets
from datetime import datetime, timezone
from typing import Any, Optional
from uuid import UUID

import psycopg2.extras
from cryptography.fernet import Fernet

from app.core.config import JWT_SECRET
from app.core.database import get_db_connection

logger = logging.getLogger(__name__)


def _get_fernet() -> Fernet:
    key = base64.urlsafe_b64encode(hashlib.sha256(JWT_SECRET.encode("utf-8")).digest())
    return Fernet(key)


def encrypt_org_token(org_id: str | UUID, org_name: str) -> str:
    """Creates a URL-safe encrypted assessment token."""
    f = _get_fernet()
    data = json.dumps({"org_id": str(org_id), "org_name": org_name}).encode("utf-8")
    enc = f.encrypt(data).decode("utf-8")
    return f"enc_{enc}"


def decrypt_org_token(token_str: str) -> Optional[dict[str, Any]]:
    """Decrypts an encrypted assessment token. Returns None if invalid or corrupted."""
    if not token_str or not isinstance(token_str, str):
        return None
    raw = token_str.strip()
    if raw.startswith("enc_"):
        raw = raw[4:]
    try:
        f = _get_fernet()
        dec = f.decrypt(raw.encode("utf-8")).decode("utf-8")
        return json.loads(dec)
    except Exception:
        return None


def generate_secure_token() -> str:
    """Generates a cryptographically random, URL-safe 256-bit access token."""
    return secrets.token_urlsafe(32)


def hash_token(raw_token: str) -> str:
    """Computes SHA-256 hash of a raw token. Only hashes are stored or queried in the database."""
    if not raw_token or not isinstance(raw_token, str):
        return ""
    return hashlib.sha256(raw_token.strip().encode("utf-8")).hexdigest()


def create_assessment_token(
    org_id: str | UUID,
    campaign_id: Optional[str | UUID] = None,
    name: Optional[str] = None,
    created_by: Optional[str] = None,
    expires_at: Optional[datetime] = None,
    is_default: bool = False,
) -> dict[str, Any]:
    """
    Creates a new secure access token for an organisation and optional campaign.
    Persists only the SHA-256 hash and preserved token. Returns the raw token once for link delivery.
    """
    raw_token = generate_secure_token()
    token_hash = hash_token(raw_token)
    oid = str(org_id)
    cid = str(campaign_id) if campaign_id else None

    with get_db_connection() as conn:
        with conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # Verify organisation exists and is active
                cur.execute("""
                    SELECT id, name, is_active, is_deleted, approval_status
                    FROM organizations
                    WHERE id = %s AND is_deleted = FALSE
                """, (oid,))
                org = cur.fetchone()
                if not org:
                    raise ValueError("Organisation not found or has been deleted.")
                if not org["is_active"]:
                    raise ValueError("Cannot create assessment link for an inactive organisation.")

                link_name = (name or "").strip() or f"{org['name']} Assessment Link"

                cur.execute("""
                    INSERT INTO assessment_access_tokens (
                        organisation_id, token_hash, token, campaign_id, name, is_default, created_by, expires_at
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id, organisation_id, campaign_id, name, is_default, created_by, created_at, expires_at
                """, (oid, token_hash, raw_token, cid, link_name, is_default, created_by, expires_at))
                row = cur.fetchone()

    return {
        "id": str(row["id"]),
        "organisation_id": str(row["organisation_id"]),
        "campaign_id": str(row["campaign_id"]) if row["campaign_id"] else None,
        "name": row["name"],
        "is_default": bool(row.get("is_default", False)),
        "created_by": row["created_by"],
        "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
        "raw_token": raw_token,
        "assessment_url": f"/audit?t={raw_token}",
    }


def get_or_create_default_token(
    org_id: str | UUID,
    created_by: Optional[str] = None,
) -> dict[str, Any]:
    """
    Retrieves the active default assessment token for an organisation, or creates one if none exists.
    Guarantees that an organisation (including historical organisations like SKY11) has an opaque,
    secure assessment link (/audit?t=SECURE_TOKEN) ready for instant copying.
    """
    oid = str(org_id)
    now = datetime.now(timezone.utc)

    try:
        with get_db_connection() as conn:
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    # 1. Check for existing active token with raw_token preserved
                    cur.execute("""
                        SELECT id, organisation_id, campaign_id, name, token, is_default, created_by, created_at, expires_at
                        FROM assessment_access_tokens
                        WHERE organisation_id = %s
                          AND revoked_at IS NULL
                          AND (expires_at IS NULL OR expires_at > %s)
                          AND token IS NOT NULL
                        ORDER BY is_default DESC, created_at DESC
                        LIMIT 1
                    """, (oid, now))
                    row = cur.fetchone()

                    if row and row.get("token"):
                        raw_token = row["token"]
                        return {
                            "id": str(row["id"]),
                            "organisation_id": str(row["organisation_id"]),
                            "campaign_id": str(row["campaign_id"]) if row["campaign_id"] else None,
                            "name": row["name"],
                            "is_default": bool(row.get("is_default", False)),
                            "created_by": row["created_by"],
                            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
                            "expires_at": row["expires_at"].isoformat() if row["expires_at"] else None,
                            "raw_token": raw_token,
                            "assessment_url": f"/audit?t={raw_token}",
                        }
    except Exception as e:
        logger.warning("Failed to lookup existing default token for %s: %s", oid, e)

    # If no active token with preserved raw_token, create a new default one
    return create_assessment_token(
        org_id=oid,
        name="Corporate Assessment Link",
        created_by=created_by or "system",
        is_default=True,
    )


def resolve_assessment_token(raw_token: str) -> dict[str, Any]:
    """
    Resolves a raw access token to its secure assessment context.
    Checks assessment_access_tokens first, then falls back to organization_invitations
    for backward compatibility.
    Validates token revocation, expiration, and organisation active/approved status.
    """
    if not raw_token or not isinstance(raw_token, str) or not raw_token.strip():
        return {
            "valid": False,
            "error": "Access token is required.",
        }

    token_hash = hash_token(raw_token)

    try:
        with get_db_connection() as conn:
            with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                # 1. Check assessment_access_tokens
                cur.execute("""
                    SELECT 
                        aat.id AS token_id,
                        aat.organisation_id,
                        aat.campaign_id,
                        aat.name AS link_name,
                        aat.expires_at,
                        aat.revoked_at,
                        o.name AS organization_name,
                        o.is_active AS org_active,
                        o.is_deleted AS org_deleted,
                        o.approval_status AS org_approval
                    FROM assessment_access_tokens aat
                    JOIN organizations o ON o.id = aat.organisation_id
                    WHERE aat.token_hash = %s
                """, (token_hash,))
                record = cur.fetchone()

                # 2. Backward compatibility fallback: check organization_invitations
                is_legacy_invitation = False
                if not record:
                    cur.execute("""
                        SELECT 
                            oi.id AS token_id,
                            oi.organization_id AS organisation_id,
                            NULL::uuid AS campaign_id,
                            oi.invitation_name AS link_name,
                            oi.expires_at,
                            oi.revoked_at,
                            oi.is_active AS inv_active,
                            oi.max_submissions,
                            oi.submission_count,
                            o.name AS organization_name,
                            o.is_active AS org_active,
                            o.is_deleted AS org_deleted,
                            o.approval_status AS org_approval
                        FROM organization_invitations oi
                        JOIN organizations o ON o.id = oi.organization_id
                        WHERE oi.token_hash = %s
                    """, (token_hash,))
                    record = cur.fetchone()
                    is_legacy_invitation = True

        if not record:
            decrypted = decrypt_org_token(raw_token)
            if decrypted and decrypted.get("org_id"):
                from app.services.org_cache_service import get_organisation_by_id, is_org_eligible
                org, _ = get_organisation_by_id(decrypted["org_id"])
                if org:
                    eligible, err = is_org_eligible(org)
                    if not eligible:
                        return {
                            "valid": False,
                            "error": err or "The organisation associated with this link is inactive.",
                        }
                    return {
                        "valid": True,
                        "token_id": "encrypted",
                        "organization_name": org["name"],
                        "organization_id": str(org["id"]),
                        "campaign_id": None,
                        "link_name": f"{org['name']} Corporate Assessment",
                        "expires_at": None,
                        "is_legacy_invitation": False,
                    }

            return {
                "valid": False,
                "error": "This assessment link is invalid or does not exist.",
            }

        # Check organisation health
        is_deleted = bool(record.get("org_deleted", False))
        is_active = bool(record.get("org_active", True))
        if is_deleted or not is_active:
            return {
                "valid": False,
                "error": "The organisation associated with this assessment link is inactive.",
            }

        if record.get("org_approval") and record["org_approval"] != "approved":
            return {
                "valid": False,
                "error": "The organisation associated with this assessment link is pending administrative approval.",
            }

        # Check revocation
        if record.get("revoked_at") is not None:
            return {
                "valid": False,
                "error": "This assessment link has been revoked.",
            }

        if is_legacy_invitation and not record.get("inv_active", True):
            return {
                "valid": False,
                "error": "This assessment link has been deactivated.",
            }

        # Check expiration
        now = datetime.now(timezone.utc)
        if record["expires_at"] and record["expires_at"] < now:
            return {
                "valid": False,
                "error": "This assessment link has expired.",
            }

        # Check submission count limit for legacy invitations
        if is_legacy_invitation and record.get("max_submissions") is not None:
            if record.get("submission_count", 0) >= record["max_submissions"]:
                return {
                    "valid": False,
                    "error": "This assessment link has reached its maximum allowed submission limit.",
                }

        token_id = str(record.get("token_id") or record.get("id") or "")
        org_id = str(record.get("organisation_id") or record.get("organization_id") or "")
        org_name = record.get("organization_name") or record.get("org_name") or ""
        link_name = record.get("link_name") or record.get("invitation_name") or "Corporate Assessment"
        campaign_id = str(record["campaign_id"]) if record.get("campaign_id") else None
        expires_at_iso = record["expires_at"].isoformat() if record.get("expires_at") else None

        return {
            "valid": True,
            "token_id": token_id,
            "organization_name": org_name,
            "organization_id": org_id,
            "campaign_id": campaign_id,
            "link_name": link_name,
            "expires_at": expires_at_iso,
            "is_legacy_invitation": is_legacy_invitation,
        }

    except Exception as e:
        logger.error("Failed to resolve assessment token: %s", e)
        raise


def revoke_assessment_token(token_id: str | UUID, revoked_by: str) -> bool:
    """Revokes an assessment access token immediately."""
    tid = str(token_id)
    with get_db_connection() as conn:
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE assessment_access_tokens
                    SET revoked_at = NOW(), revoked_by = %s
                    WHERE id = %s AND revoked_at IS NULL
                """, (revoked_by, tid))
                return cur.rowcount > 0

```

#### `app/services/user_service.py`

```python
"""
user_service.py — Administrator user management services
Enforces role validation ('admin', 'super') and prevents accidental deletion or demotion of the last Super Admin.
"""
import psycopg2.extras
from fastapi import HTTPException

VALID_ROLES = {"admin", "super"}

def verify_user(conn, email: str) -> dict:
    """Check if an email exists in admin_users and return role."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
            (email.strip(),),
        )
        row = cur.fetchone()
        
    if row:
        return {"authorized": True, "role": row["role"]}
    return {"authorized": False}


def get_users(conn) -> list:
    """Get all admin users."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, email, role, created_at FROM admin_users ORDER BY created_at DESC")
        return cur.fetchall()


def add_user(conn, email: str, role: str) -> dict:
    """
    Add a new administrator or update an existing administrator's role.
    Validates role and ensures the last Super Admin cannot be demoted.
    """
    email_clean = email.strip().lower()
    role_clean = role.strip().lower()
    
    if role_clean not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Allowed roles are: {', '.join(sorted(VALID_ROLES))}"
        )
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Check if user already exists
        cur.execute(
            "SELECT id, email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
            (email_clean,)
        )
        existing = cur.fetchone()
        
        # If user is currently a super admin and being demoted to admin
        if existing and existing["role"] == "super" and role_clean != "super":
            cur.execute("SELECT COUNT(*) as count FROM admin_users WHERE role = 'super'")
            super_count = cur.fetchone()["count"]
            if super_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot demote the last remaining Super Admin. At least one Super Admin must exist."
                )
        
        if existing:
            cur.execute(
                "UPDATE admin_users SET role = %s WHERE LOWER(email) = LOWER(%s) RETURNING id, email, role, created_at",
                (role_clean, email_clean)
            )
            row = cur.fetchone()
        else:
            cur.execute(
                "INSERT INTO admin_users (email, role) VALUES (%s, %s) RETURNING id, email, role, created_at",
                (email_clean, role_clean)
            )
            row = cur.fetchone()
            
        conn.commit()
        return dict(row)


def remove_user(conn, email: str) -> bool:
    """
    Remove an administrator user.
    Prevents deletion of the last remaining Super Admin.
    """
    email_clean = email.strip().lower()
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
            (email_clean,)
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["role"] == "super":
            cur.execute("SELECT COUNT(*) as count FROM admin_users WHERE role = 'super'")
            super_count = cur.fetchone()["count"]
            if super_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete the last remaining Super Admin. At least one Super Admin must exist."
                )
        
        cur.execute("DELETE FROM admin_users WHERE LOWER(email) = LOWER(%s)", (email_clean,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted

```

_…and 1 more file(s) not shown._

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

