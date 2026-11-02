"""
migrate.py — Canonical NIWI database migration runner.
Tracks migration execution in the `schema_migrations` table for idempotency.
Applies migrations in sorted numerical order inside individual transactions.

Usage:
  python scripts/migrate.py              # Apply all pending migrations
  python scripts/migrate.py --status     # Show migration status
  python scripts/migrate.py <file_name>  # Apply a specific migration
"""
import sys
import os
import glob
from pathlib import Path

# Add project root to path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.config import APP_ENV, IS_PRODUCTION
from app.core.database import get_conn, is_production_database

MIGRATIONS_DIR = ROOT / "migrations"


def get_migration_files():
    """Return all migration SQL files in sorted order."""
    return sorted(MIGRATIONS_DIR.glob("*.sql"))


def ensure_migration_table(conn):
    """Ensure the schema_migrations tracking table exists."""
    with conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS schema_migrations (
                version VARCHAR(255) PRIMARY KEY,
                applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
            );
        """)
    conn.commit()


def get_applied_migrations(conn):
    """Return set of migration filenames that have already been applied."""
    ensure_migration_table(conn)
    with conn.cursor() as cur:
        cur.execute("SELECT version FROM schema_migrations;")
        return {row[0] for row in cur.fetchall()}


def run_migration_file(conn, file_path: Path):
    """Execute a single migration file in a transaction and record it."""
    version = file_path.name
    with open(file_path, "r", encoding="utf-8") as f:
        sql = f.read()

    with conn:
        with conn.cursor() as cur:
            cur.execute(sql)
            cur.execute(
                "INSERT INTO schema_migrations (version) VALUES (%s) ON CONFLICT (version) DO NOTHING;",
                (version,)
            )
    print(f"  [APPLIED] {version}")


def show_status():
    """Display status of all migrations."""
    conn = get_conn()
    try:
        applied = get_applied_migrations(conn)
        all_files = get_migration_files()
        print("\nMigration Status:")
        print("-" * 60)
        for f in all_files:
            status = "APPLIED" if f.name in applied else "PENDING"
            print(f"  [{status:<7}] {f.name}")
        print("-" * 60)
    finally:
        conn.close()


def migrate(target_file: str = None):
    """Run pending migrations."""
    conn = get_conn()
    try:
        ensure_migration_table(conn)
        applied = get_applied_migrations(conn)
        all_files = get_migration_files()

        if target_file:
            matching = [f for f in all_files if f.name == target_file or target_file in f.name]
            if not matching:
                print(f"Error: Migration file matching '{target_file}' not found.")
                sys.exit(1)
            target = matching[0]
            if target.name in applied:
                print(f"Migration {target.name} is already recorded as applied.")
                return
            print(f"Applying single migration: {target.name}")
            run_migration_file(conn, target)
            return

        pending = [f for f in all_files if f.name not in applied]
        if not pending:
            print("\nDatabase is up to date. No pending migrations.")
            return

        print(f"\nApplying {len(pending)} pending migration(s)...")
        for f in pending:
            run_migration_file(conn, f)

        print("\nAll pending migrations applied successfully.")
    finally:
        conn.close()


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] in ("--status", "-s"):
        show_status()
    elif len(sys.argv) > 1 and not sys.argv[1].startswith("-"):
        migrate(sys.argv[1])
    else:
        migrate()
