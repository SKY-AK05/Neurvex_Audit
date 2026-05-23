"""
seed_db.py — Seed the database with sample submissions for local testing.
Run: python scripts/seed_db.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import get_conn
from app.services.scoring_service import calculate_scores

SAMPLES = [
    {"name": "Sarah Mitchell", "company_name": "Brightpath Solutions",
     "email": "sarah@brightpath.co.uk", "contact_number": "+44 7700 123456",
     **{f"q{i}": "Yes" for i in range(5, 45)}},
    {"name": "James Okafor", "company_name": "Nexgen Retail Group",
     "email": "j.okafor@nexgen.com", "contact_number": None,
     **{f"q{i}": ("Partially" if i % 2 == 0 else "No") for i in range(5, 45)}},
]

def seed():
    conn = get_conn()
    for s in SAMPLES:
        scores = calculate_scores(s)
        params = {**s, **scores}
        with conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO submissions (name, company_name, email, contact_number,
                        lc_score, lc_level, ro_score, ro_level, we_score, we_level,
                        be_score, be_level, tm_score, tm_level, ca_score, ca_level,
                        pc_score, pc_level, sp_score, sp_level,
                        overall_avg, overall_level, email_body, status)
                    VALUES (%(name)s, %(company_name)s, %(email)s, %(contact_number)s,
                        %(lc_score)s, %(lc_level)s, %(ro_score)s, %(ro_level)s,
                        %(we_score)s, %(we_level)s, %(be_score)s, %(be_level)s,
                        %(tm_score)s, %(tm_level)s, %(ca_score)s, %(ca_level)s,
                        %(pc_score)s, %(pc_level)s, %(sp_score)s, %(sp_level)s,
                        %(overall_avg)s, %(overall_level)s, %(email_body)s, 'pending')
                """, params)
        print(f"Seeded: {s['name']}")
    conn.close()

if __name__ == "__main__":
    seed()
