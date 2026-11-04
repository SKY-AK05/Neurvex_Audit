"""
run_migration.py — Run migrations against the live database.
Usage:
  python scripts/run_migration.py                       # Runs all pending migrations via migrate.py
  python scripts/run_migration.py <migration_file>      # Runs a specific migration file
"""
import os
import sys
import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

if len(sys.argv) <= 1:
    # Default to running all pending migrations safely via migrate.py
    from scripts.migrate import migrate
    migrate()
    sys.exit(0)

from app.core.keyvault import init_keyvault, get_database_config

init_keyvault()
db_config = get_database_config()
migration_file = sys.argv[1]

print(f"Running specific migration: {migration_file}")

conn = psycopg2.connect(
    host=db_config["host"],
    dbname=db_config["database"],
    user=db_config["user"],
    password=db_config["password"],
    port=db_config["port"],
    sslmode="require",
)

try:
    with open(migration_file, "r", encoding="utf-8") as f:
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
