import os
import sys
import dotenv
dotenv.load_dotenv()
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.core.database import get_conn

conn = get_conn()
cur = conn.cursor()

# 1. Total submissions
cur.execute("SELECT count(*) FROM submissions;")
print("Total Submissions in DB:", cur.fetchone()[0])

# 2. Nexora org check
cur.execute("""
    SELECT o.id, o.name, count(osl.submission_id)
    FROM organizations o
    LEFT JOIN org_submission_links osl ON osl.org_id = o.id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY o.id, o.name;
""")
print("Nexora in organizations table:", cur.fetchone())

# 3. Demographics check for Nexora
cur.execute("""
    SELECT 
        answers->>'role' as role,
        count(*)
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY answers->>'role'
    ORDER BY count(*) DESC;
""")
print("\nRole distribution in Nexora:")
for r in cur.fetchall():
    print(" ", r)

# 4. Age groups check
cur.execute("""
    SELECT 
        answers->>'age_group' as age_group,
        count(*)
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY answers->>'age_group'
    ORDER BY count(*) DESC;
""")
print("\nAge group distribution in Nexora:")
for r in cur.fetchall():
    print(" ", r)

# 5. Neurodiversity check
cur.execute("""
    SELECT 
        answers->>'is_neurodivergent' as is_nd,
        count(*)
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    GROUP BY answers->>'is_neurodivergent'
    ORDER BY count(*) DESC;
""")
print("\nNeurodiversity Identification in Nexora:")
for r in cur.fetchall():
    print(" ", r)

# 6. Sample employee check
cur.execute("""
    SELECT s.name, s.designation, s.email, s.contact_number, s.overall_avg, s.overall_level, s.answers->>'employee_id'
    FROM submissions s
    JOIN organizations o ON o.id = s.organization_id
    WHERE o.name = 'Nexora Technologies'
    ORDER BY s.submitted_at ASC
    LIMIT 3;
""")
print("\nSample imported employees:")
for r in cur.fetchall():
    print(" ", r)

cur.close()
conn.close()
