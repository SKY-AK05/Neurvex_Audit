"""
migrate.py — Run database migrations.
Applies create_table.sql, then all numbered migration files in migrations/.
Run: python scripts/migrate.py
"""
import sys, os, glob
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Load .env so database credentials are available
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.core.database import get_conn

ROOT       = os.path.join(os.path.dirname(__file__), "..")
BASE_SQL   = os.path.join(ROOT, "create_table.sql")
MIGRATIONS = sorted(glob.glob(os.path.join(ROOT, "migrations", "*.sql")))

def run_sql(conn, path):
    with open(path) as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"  [OK] {os.path.basename(path)}")

def migrate():
    conn = get_conn()
    print("Running base schema...")
    run_sql(conn, BASE_SQL)

    if MIGRATIONS:
        print("Running migrations...")
        for path in MIGRATIONS:
            run_sql(conn, path)

    conn.close()
    print("\nAll migrations complete.")

if __name__ == "__main__":
    migrate()
