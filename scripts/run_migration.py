"""
run_migration.py — Run a specific SQL migration against the live database.
Usage: python run_migration.py <migration_file>
Example: python run_migration.py migrations/007_fix_score_columns.sql
"""
import os
import sys
import psycopg2
from dotenv import load_dotenv

load_dotenv()

migration_file = sys.argv[1] if len(sys.argv) > 1 else "migrations/007_fix_score_columns.sql"

print(f"Running migration: {migration_file}")

conn = psycopg2.connect(
    host=os.environ["PGHOST"],
    dbname=os.environ.get("PGDATABASE", "nd_audit"),
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
    port=os.environ.get("PGPORT", "5432"),
    sslmode="require",
)

try:
    with open(migration_file, "r") as f:
        sql = f.read()

    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)

    print(f"✅ Migration applied successfully: {migration_file}")
except Exception as e:
    print(f"❌ Migration failed: {e}")
    conn.rollback()
    sys.exit(1)
finally:
    conn.close()
