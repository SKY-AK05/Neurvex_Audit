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
        return html_module.escape(str(t))

    subject_line = f"[NeuroMark Support] {subject.strip()}"
    plain = (
        f"New support request from NeuroMark\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{message}\n"
    )
    html = (
        "<p><strong>New support request</strong> from NeuroMark</p>"
        f"<p><strong>Name:</strong> {esc(name)}<br>"
        f"<strong>Email:</strong> <a href=\"mailto:{esc(email)}\">{esc(email)}</a><br>"
        f"<strong>Subject:</strong> {esc(subject)}</p>"
        f"<p><strong>Message:</strong></p>"
        f"<p style=\"white-space:pre-wrap;line-height:1.6;\">{esc(message)}</p>"
    )

    client = EmailClient.from_connection_string(os.environ["ACS_CONNECTION_STRING"])
    acs_message = {
        "senderAddress": sender_address,
        "recipients": {"to": [{"address": to_address, "displayName": "Orchvate Support"}]},
        "content": {"subject": subject_line, "html": html, "plainText": plain},
        "replyTo": [{"address": email.strip(), "displayName": name.strip() or email.strip()}],
    }
    poller = client.begin_send(acs_message)
    poller.result()


def send_admin_submission_digest(batch_limit: int = 500) -> int:
    """
    Batched 5-minute digest notification for admins.
    Collects all audits processed into submissions with admin_notify_status = 'QUEUED_DIGEST',
    sends ONE consolidated digest email, and marks them 'DIGEST_SENT'.
    If 0 audits arrived, sends nothing.
    """
    from app.core.database import get_db_connection

    try:
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                settings = get_settings(cur)
                if not settings.get("notifications_enabled", False):
                    # Drain queue without sending if notifications are disabled
                    with conn:
                        with conn.cursor() as upd_cur:
                            upd_cur.execute(
                                "UPDATE submissions SET admin_notify_status = 'SKIPPED' WHERE admin_notify_status = 'QUEUED_DIGEST';"
                            )
                    return 0

                cur.execute(
                    """
                    SELECT id, name, company_name, designation, email, submitted_at, overall_avg, overall_level
                    FROM submissions
                    WHERE admin_notify_status = 'QUEUED_DIGEST'
                    ORDER BY submitted_at ASC
                    LIMIT %s;
                    """,
                    (batch_limit,)
                )
                rows = cur.fetchall()

        if not rows:
            return 0

        # Filter out synthetic load test submissions from notification count
        real_rows = []
        for r in rows:
            email_val = str(r[4] or "").lower()
            name_val = str(r[1] or "").lower()
            if "example.com" in email_val or "loadtest_" in email_val or "synthetic" in name_val:
                continue
            real_rows.append(r)

        sub_ids = [str(r[0]) for r in rows]

        if not real_rows:
            # All were synthetic test rows, mark them processed without spamming admin
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE submissions SET admin_notify_status = 'SKIPPED' WHERE id = ANY(%s::uuid[]);",
                            (sub_ids,)
                        )
            return len(sub_ids)

        total_count = len(real_rows)

        # Group by company name for a clear breakdown
        org_counts = {}
        for r in real_rows:
            c_name = r[2] or "Direct / Independent"
            org_counts[c_name] = org_counts.get(c_name, 0) + 1

        def esc(t):
            return html_module.escape(str(t))

        org_breakdown_html = "".join(
            f"<tr><td style='padding:8px 12px;border:1px solid #E2E8F0;font-weight:600;'>{esc(org)}</td><td style='padding:8px 12px;border:1px solid #E2E8F0;text-align:right;'>{cnt}</td></tr>"
            for org, cnt in sorted(org_counts.items(), key=lambda x: x[1], reverse=True)
        )
        org_breakdown_text = "\n".join(
            f"  - {org}: {cnt} submission(s)"
            for org, cnt in sorted(org_counts.items(), key=lambda x: x[1], reverse=True)
        )

        admin_emails = [e.strip() for e in (settings.get("notification_email") or "").replace(";", ",").split(",") if e.strip()]
        if not admin_emails:
            logger.warning("Admin digest: notifications enabled but no notification_email configured")
            return 0

        cc_emails = [e.strip() for e in (settings.get("notification_cc_email") or "").replace(";", ",").split(",") if e.strip()]
        sender_address, sender_name = get_sender_for_send(None)
        if not sender_address:
            logger.warning("Admin digest: no sender address configured")
            return 0

        if not is_acs_configured():
            logger.info("Admin digest: ACS not configured, marking %d submissions as SKIPPED", total_count)
            with get_db_connection() as conn:
                with conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            "UPDATE submissions SET admin_notify_status = 'SKIPPED' WHERE id = ANY(%s::uuid[]);",
                            (sub_ids,)
                        )
            return total_count

        frontend_base = os.environ.get("FRONTEND_URL", "https://taiga.orchvate.com").rstrip("/")
        dashboard_url = f"{frontend_base}/admin/dashboard"

        subject = f"NeuroMark Digest: {total_count} New Audit{'s' if total_count > 1 else ''} Received"
        plain = (
            f"NeuroMark 5-Minute Audit Digest\n"
            f"=================================\n\n"
            f"In the last 5 minutes, {total_count} new audit submission(s) were received and processed.\n\n"
            f"Breakdown by Organisation:\n"
            f"{org_breakdown_text}\n\n"
            f"Open Admin Dashboard: {dashboard_url}\n"
        )
        html = (
            f"<div style='font-family:-apple-system,BlinkMacSystemFont,\"Segoe UI\",Roboto,sans-serif;color:#161057;max-width:600px;margin:0 auto;padding:20px;border:1px solid #E2E8F0;border-radius:8px;background:#FAF9F5;'>"
            f"<h2 style='color:#161057;margin-top:0;'>NeuroMark Audit Digest</h2>"
            f"<p style='font-size:15px;color:#475569;'>In the past 5 minutes, <strong>{total_count}</strong> new audit submission{'s have' if total_count > 1 else ' has'} been received and processed.</p>"
            f"<table style='width:100%;border-collapse:collapse;margin:16px 0;background:#FFFFFF;'>"
            f"<thead><tr style='background:#F1F5F9;'><th style='padding:8px 12px;border:1px solid #E2E8F0;text-align:left;'>Organisation</th><th style='padding:8px 12px;border:1px solid #E2E8F0;text-align:right;'>Audits</th></tr></thead>"
            f"<tbody>{org_breakdown_html}</tbody>"
            f"</table>"
            f"<div style='margin-top:20px;'>"
            f"<a href='{dashboard_url}' style='display:inline-block;background:#161057;color:#FFFFFF;padding:10px 22px;border-radius:6px;text-decoration:none;font-weight:600;'>Open Admin Dashboard →</a>"
            f"</div>"
            f"</div>"
        )

        send_acs_email(
            to_addresses=admin_emails,
            cc_addresses=cc_emails if cc_emails else None,
            subject=subject,
            html=html,
            plain=plain,
            sender_address=sender_address,
            sender_name=sender_name,
        )
        logger.info("Admin 5-minute digest sent successfully for %d submissions", total_count)

        with get_db_connection() as conn:
            with conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "UPDATE submissions SET admin_notify_status = 'DIGEST_SENT' WHERE id = ANY(%s::uuid[]);",
                        (sub_ids,)
                    )
        return total_count
    except Exception as e:
        logger.error("Failed to send admin submission digest: %s", e, exc_info=True)
        return 0
