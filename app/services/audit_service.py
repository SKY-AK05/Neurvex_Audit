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
