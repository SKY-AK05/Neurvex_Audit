"""
Settings and admin notification emails.
"""

import html as html_module
import logging
import os
from typing import Tuple

from azure.communication.email import EmailClient

logger = logging.getLogger(__name__)

DEFAULT_SUPPORT_EMAIL = "aakash.padyachi@rochvate.com"


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
                    updated_at              TIMESTAMP DEFAULT NOW()
                );
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


def get_settings(cur) -> dict:
    ensure_settings_row(cur)
    cur.execute(
        """
        SELECT sender_name, sender_address, notification_email, notification_cc_email,
               notifications_enabled, support_email, updated_at
        FROM app_settings WHERE id = 1
        """
    )
    row = cur.fetchone()
    if not row:
        env = _env_sender()
        return {
            "sender_name": env["sender_name"],
            "sender_address": env["sender_address"],
            "notification_email": "",
            "notification_cc_email": "",
            "notifications_enabled": False,
            "support_email": DEFAULT_SUPPORT_EMAIL,
            "updated_at": None,
        }
    return {
        "sender_name": row[0] or _env_sender()["sender_name"],
        "sender_address": row[1] or _env_sender()["sender_address"],
        "notification_email": row[2] or "",
        "notification_cc_email": row[3] or "",
        "notifications_enabled": bool(row[4]),
        "support_email": (row[5] or "").strip() or DEFAULT_SUPPORT_EMAIL,
        "updated_at": row[6].isoformat() if row[6] else None,
    }


def update_settings(cur, data: dict) -> dict:
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

    cur.execute(
        """
        UPDATE app_settings SET
            sender_name = %s,
            sender_address = %s,
            notification_email = %s,
            notification_cc_email = %s,
            notifications_enabled = %s,
            support_email = %s,
            updated_at = NOW()
        WHERE id = 1
        """,
        (sender_name, sender_address, notification_email, notification_cc_email, notifications_enabled, support_email),
    )
    return get_settings(cur)


def get_sender_for_send(cur) -> Tuple[str, str]:
    settings = get_settings(cur)
    env = _env_sender()
    address = settings["sender_address"] or env["sender_address"]
    name = settings["sender_name"] or env["sender_name"]
    return address, name


def send_acs_email(*, to_addresses: list[str] = None, to_address: str = None, to_name: str = "", cc_addresses: list[str] = None, subject: str, html: str, plain: str,
                   sender_address: str, sender_name: str) -> None:
    client = EmailClient.from_connection_string(os.environ["ACS_CONNECTION_STRING"])
    
    to_recipients = [{"address": a.strip()} for a in to_addresses if a.strip()] if to_addresses else [{"address": to_address, "displayName": to_name}]
    message = {
        "senderAddress": sender_address,
        "recipients": {"to": to_recipients},
        "content": {"subject": subject, "html": html, "plainText": plain},
        "replyTo": [{"address": sender_address, "displayName": sender_name}],
    }
    
    if cc_addresses:
        cc_recipients = [{"address": c.strip()} for c in cc_addresses if c.strip()]
        if cc_recipients:
            message["recipients"]["cc"] = cc_recipients

    poller = client.begin_send(message)
    poller.result()


def notify_admin_new_submission(cur, submission_id: int, name: str, company_name: str) -> bool:
    """Send admin alert if notifications are enabled. Returns True if email was sent."""
    settings = get_settings(cur)
    if not settings["notifications_enabled"]:
        return False
    admin_emails = [e.strip() for e in (settings["notification_email"] or "").replace(";", ",").split(",") if e.strip()]
    if not admin_emails:
        logger.warning("Notifications enabled but notification_email is empty")
        return False
        
    cc_emails = [e.strip() for e in (settings.get("notification_cc_email") or "").replace(";", ",").split(",") if e.strip()]

    sender_address, sender_name = get_sender_for_send(cur)
    if not sender_address:
        logger.error("No sender address configured for admin notification")
        return False

    frontend_base = os.environ.get("FRONTEND_URL", "http://localhost:5173").rstrip("/")
    review_url = f"{frontend_base}/admin/submissions/{submission_id}"

    subject = f"New audit to review — {company_name}"
    plain = (
        f"A new Neurvex Audit has been submitted.\n\n"
        f"Organisation: {company_name}\n"
        f"Respondent: {name}\n"
        f"Submission ID: {submission_id}\n\n"
        f"Review the submission: {review_url}\n"
    )
    html = (
        f"<p>A new <strong>Neurvex Audit</strong> has been submitted and is ready for your review.</p>"
        f"<p><strong>Organisation:</strong> {company_name}<br>"
        f"<strong>Respondent:</strong> {name}<br>"
        f"<strong>Submission ID:</strong> {submission_id}</p>"
        f'<p><a href="{review_url}">Open submission in Neurvex</a></p>'
    )

    try:
        import threading
        
        def bg_send():
            try:
                send_acs_email(
                    to_addresses=admin_emails,
                    cc_addresses=cc_emails,
                    subject=subject,
                    html=html,
                    plain=plain,
                    sender_address=sender_address,
                    sender_name=sender_name,
                )
            except Exception as e:
                logger.error("Background admin notification failed: %s", e)
                
        threading.Thread(target=bg_send).start()
        return True
    except Exception as e:
        logger.error("Failed to start admin notification thread: %s", e)
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

    subject_line = f"[Neurvex Support] {subject.strip()}"
    plain = (
        f"New support request from Neurvex\n\n"
        f"Name: {name}\n"
        f"Email: {email}\n"
        f"Subject: {subject}\n\n"
        f"Message:\n{message}\n"
    )
    html = (
        "<p><strong>New support request</strong> from Neurvex</p>"
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
