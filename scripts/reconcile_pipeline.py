"""
reconcile_pipeline.py — Comprehensive Submission Pipeline Reconciliation Tool
Verifies end-to-end durability and accounting across:
1. Submissions sent / acknowledged
2. Records persisted in raw_submissions
3. Outbox events staged and dispatched in service_bus_outbox
4. Final completed records in submissions table
5. Dead-lettered or retrying records
6. Records visible in the admin dashboard query
"""
import os
import sys
import json
import logging
from typing import Optional, Dict, Any

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2.extras
from app.core.database import get_db_connection

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("reconcile")


def reconcile_pipeline(test_run_prefix: Optional[str] = None) -> Dict[str, Any]:
    """Run full pipeline reconciliation."""
    with get_db_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            # 1. raw_submissions counts
            where_raw = ""
            params_raw = ()
            if test_run_prefix:
                where_raw = "WHERE idempotency_key LIKE %s"
                params_raw = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT status, COUNT(*) AS count
                FROM raw_submissions
                {where_raw}
                GROUP BY status
            """, params_raw)
            raw_by_status = {r["status"]: r["count"] for r in cur.fetchall()}
            raw_total = sum(raw_by_status.values())

            # 2. service_bus_outbox counts
            where_outbox = ""
            params_outbox = ()
            if test_run_prefix:
                where_outbox = "WHERE payload->>'idempotency_key' LIKE %s"
                params_outbox = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT status, COUNT(*) AS count
                FROM service_bus_outbox
                {where_outbox}
                GROUP BY status
            """, params_outbox)
            outbox_by_status = {r["status"]: r["count"] for r in cur.fetchall()}
            outbox_total = sum(outbox_by_status.values())

            # 3. submissions table counts
            where_sub = ""
            params_sub = ()
            if test_run_prefix:
                where_sub = "WHERE idempotency_key LIKE %s"
                params_sub = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT status, async_status, COUNT(*) AS count
                FROM submissions
                {where_sub}
                GROUP BY status, async_status
            """, params_sub)
            sub_rows = cur.fetchall()
            sub_total = sum(r["count"] for r in sub_rows)
            sub_completed = sum(r["count"] for r in sub_rows if r["status"] == "completed" or r["async_status"] == "COMPLETED")

            # 4. Check for orphaned raw submissions (accepted but never reached submissions)
            where_orphans = "WHERE r.status = 'COMPLETED' AND s.id IS NULL"
            params_orphans = ()
            if test_run_prefix:
                where_orphans += " AND r.idempotency_key LIKE %s"
                params_orphans = (f"%{test_run_prefix}%",)

            cur.execute(f"""
                SELECT COUNT(*) AS count
                FROM raw_submissions r
                LEFT JOIN submissions s ON (s.id = r.submission_id OR s.raw_submission_id = r.submission_id)
                {where_orphans}
            """, params_orphans)
            orphan_count = cur.fetchone()["count"]

            # 5. Check dead-lettered / failed submissions
            dead_letter_count = raw_by_status.get("DEAD_LETTERED", 0) + raw_by_status.get("FAILED", 0)

            # 6. Dashboard query visibility test
            if test_run_prefix:
                cur.execute("""
                    SELECT COUNT(*) AS count FROM (
                        SELECT id FROM submissions WHERE email LIKE %(p)s
                        UNION ALL
                        SELECT r.submission_id AS id
                        FROM raw_submissions r
                        WHERE r.status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING')
                          AND (r.payload->>'email' LIKE %(p)s)
                          AND NOT EXISTS (
                              SELECT 1 FROM submissions s WHERE s.id = r.submission_id OR s.raw_submission_id = r.submission_id
                          )
                    ) dash
                """, {"p": f"%{test_run_prefix}%"})
            else:
                cur.execute("""
                    SELECT COUNT(*) AS count FROM (
                        SELECT id FROM submissions
                        UNION ALL
                        SELECT r.submission_id AS id
                        FROM raw_submissions r
                        WHERE r.status IN ('RECEIVED', 'PROCESSING', 'DEAD_LETTERED', 'FAILED', 'RETRYING')
                          AND NOT EXISTS (
                              SELECT 1 FROM submissions s WHERE s.id = r.submission_id OR s.raw_submission_id = r.submission_id
                          )
                    ) dash
                """)
            dashboard_visible = cur.fetchone()["count"]

    report = {
        "filter_prefix": test_run_prefix or "ALL",
        "raw_submissions_total": raw_total,
        "raw_by_status": raw_by_status,
        "outbox_total": outbox_total,
        "outbox_by_status": outbox_by_status,
        "submissions_total": sub_total,
        "submissions_completed": sub_completed,
        "orphans_completed_without_submission": orphan_count,
        "dead_letter_or_failed": dead_letter_count,
        "dashboard_visible_total": dashboard_visible
    }

    # Print clean formatted table
    print("\n" + "=" * 65)
    print(f"  NIWI SUBMISSION PIPELINE RECONCILIATION [{report['filter_prefix']}]")
    print("=" * 65)
    print(f"  Raw Submissions Staged:         {raw_total:>6}")
    for st, cnt in sorted(raw_by_status.items()):
        print(f"    - {st:<25} {cnt:>6}")
    print("-" * 65)
    print(f"  Outbox Records Created:         {outbox_total:>6}")
    for st, cnt in sorted(outbox_by_status.items()):
        print(f"    - {st:<25} {cnt:>6}")
    print("-" * 65)
    print(f"  Final Submissions Persisted:    {sub_total:>6}")
    print(f"    - Completed & Scored:         {sub_completed:>6}")
    print(f"  Dead-Lettered / Failed:         {dead_letter_count:>6}")
    print(f"  Orphaned Unpromoted Rows:       {orphan_count:>6}")
    print(f"  Submissions Visible in Dash:    {dashboard_visible:>6}")
    print("=" * 65)

    discrepancy = raw_total - (sub_completed + dead_letter_count + raw_by_status.get("RECEIVED", 0) + raw_by_status.get("PROCESSING", 0) + raw_by_status.get("RETRYING", 0))
    if discrepancy == 0 and orphan_count == 0:
        print("  [PASS] ZERO LOSS RECONCILIATION: 100% of submissions accounted for.")
    else:
        print(f"  [WARN] Discrepancy of {discrepancy} rows detected between raw and final records.")
    print("=" * 65 + "\n")

    return report


if __name__ == "__main__":
    prefix = sys.argv[1] if len(sys.argv) > 1 else None
    reconcile_pipeline(prefix)
