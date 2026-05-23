"""
set_super.py — Force-set aakash.padyachi@orchvate.com to role='super'.
Run: python scripts/set_super.py
"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.core.database import get_conn

SUPER_EMAIL = "aakash.padyachi@orchvate.com"

conn = get_conn()
with conn.cursor() as cur:
    # Upsert: insert if not exists, always set role to super
    cur.execute("""
        INSERT INTO admin_users (email, role)
        VALUES (%s, 'super')
        ON CONFLICT (email) DO UPDATE SET role = 'super'
    """, (SUPER_EMAIL,))
    
    # Confirm
    cur.execute("SELECT email, role FROM admin_users WHERE email = %s", (SUPER_EMAIL,))
    row = cur.fetchone()
    print(f"Updated: {row}")

conn.commit()
conn.close()
print("Done. Aakash is now Super Admin.")
