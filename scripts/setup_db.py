"""
setup_db.py — Creates the nd_audit database and submissions table on Azure PostgreSQL.
Run once: python scripts/setup_db.py
"""
import psycopg2
import os
from pathlib import Path

# Load .env manually (no dotenv dependency needed)
env_path = Path(__file__).parent.parent / ".env"
for line in env_path.read_text().splitlines():
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip())

HOST     = os.environ["PGHOST"]
PORT     = os.environ.get("PGPORT", "5432")
USER     = os.environ["PGUSER"]
PASSWORD = os.environ["PGPASSWORD"]

def run(conn, sql):
    with conn.cursor() as cur:
        cur.execute(sql)

# Step 1 — connect to the default 'postgres' db and create nd_audit if needed
print("Connecting to Azure PostgreSQL...")
conn = psycopg2.connect(
    host=HOST, port=PORT, dbname="postgres",
    user=USER, password=PASSWORD, sslmode="require"
)
conn.autocommit = True

with conn.cursor() as cur:
    cur.execute("SELECT 1 FROM pg_database WHERE datname = 'nd_audit'")
    exists = cur.fetchone()

if not exists:
    with conn.cursor() as cur:
        cur.execute("CREATE DATABASE nd_audit")
    print("Created database: nd_audit")
else:
    print("Database nd_audit already exists, skipping.")

conn.close()

# Step 2 — connect to nd_audit and create the submissions table
conn2 = psycopg2.connect(
    host=HOST, port=PORT, dbname="nd_audit",
    user=USER, password=PASSWORD, sslmode="require"
)
conn2.autocommit = True

sql = Path(__file__).parent.parent / "create_table.sql"
ddl = sql.read_text()

# Strip out the commented CREATE DATABASE line so it doesn't error
ddl_clean = "\n".join(
    l for l in ddl.splitlines()
    if not l.strip().startswith("--") and l.strip()
)

with conn2.cursor() as cur:
    cur.execute(ddl_clean)

conn2.close()
print("submissions table ready.")
print("\nAll done. You can now run: func start")
