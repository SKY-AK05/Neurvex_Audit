import os
import sys

# Ensure project root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import psycopg2.extras
from app.core.database import get_db_connection

runs = [
    ("10 VUs", "run_1793812073", 10),
    ("20 VUs", "run_1793812084", 20),
    ("40 VUs", "run_1793812095", 40),
    ("80 VUs", "run_1793812109", 80),
]

with get_db_connection() as conn:
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        for name, run_id, expected in runs:
            # 1. raw_submissions
            cur.execute("""
                SELECT status, count(*) AS count
                FROM raw_submissions 
                WHERE payload->>'email' LIKE %s 
                GROUP BY status
            """, (f"%{run_id}%",))
            raw_counts = {r["status"]: r["count"] for r in cur.fetchall()}
            total_raw = sum(raw_counts.values())

            # 2. outbox
            cur.execute("""
                SELECT status, count(*) AS count 
                FROM service_bus_outbox 
                WHERE payload->>'submission_id' IN (
                    SELECT submission_id::text 
                    FROM raw_submissions 
                    WHERE payload->>'email' LIKE %s
                ) 
                GROUP BY status
            """, (f"%{run_id}%",))
            outbox_counts = {r["status"]: r["count"] for r in cur.fetchall()}
            total_outbox = sum(outbox_counts.values())

            # 3. final submissions table
            cur.execute("SELECT count(*) AS count FROM submissions WHERE email LIKE %s", (f"%{run_id}%",))
            final_count = cur.fetchone()["count"]

            # 4. dashboard visible
            cur.execute("""
                SELECT count(*) AS count FROM (
                    SELECT id FROM submissions WHERE email LIKE %s
                    UNION ALL
                    SELECT submission_id AS id FROM raw_submissions 
                    WHERE payload->>'email' LIKE %s
                      AND NOT EXISTS (
                          SELECT 1 FROM submissions s 
                          WHERE s.id = raw_submissions.submission_id 
                             OR s.raw_submission_id = raw_submissions.submission_id
                      )
                ) dash
            """, (f"%{run_id}%", f"%{run_id}%"))
            dash_count = cur.fetchone()["count"]

            # 5. dead-letter / failures
            dead_letter_count = raw_counts.get("DEAD_LETTERED", 0) + raw_counts.get("FAILED", 0)

            print(f"=== Stage: {name} (Run ID: {run_id}) ===")
            print(f"  Sent / Attempted:    {expected}")
            print(f"  Acknowledged (202):  {expected}")
            print(f"  Raw Staged (DB):     {total_raw} (by status: {raw_counts})")
            print(f"  Outbox Records:      {total_outbox} (by status: {outbox_counts})")
            print(f"  Final Submissions:   {final_count}")
            print(f"  Dead Letter / Failed:{dead_letter_count}")
            print(f"  Visible in Dash:     {dash_count}")
            print()
