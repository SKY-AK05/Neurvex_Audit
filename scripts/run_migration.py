"""
run_migration.py — Run a specific SQL migration against the live database.
Usage: python run_migration.py <migration_file>
Example: python run_migration.py migrations/007_fix_score_columns.sql
"""
import os
import sys
import psycopg2

# Add app directory to path to import keyvault module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from app.core.keyvault import init_keyvault, get_database_config

# Initialize Key Vault (falls back to env vars in dev)
init_keyvault()

# Get database config from Key Vault or environment
db_config = get_database_config()

migration_file = sys.argv[1] if len(sys.argv) > 1 else "migrations/007_fix_score_columns.sql"

print(f"Running migration: {migration_file}")

conn = psycopg2.connect(
    host=db_config["host"],
    dbname=db_config["database"],
    user=db_config["user"],
    password=db_config["password"],
    port=db_config["port"],
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
