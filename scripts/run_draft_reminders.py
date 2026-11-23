"""
scripts/run_draft_reminders.py — Standalone CLI runner to trigger draft reminder checks.
Can be invoked by Azure Functions, Cron, or manual operator commands.
Usage:
    python scripts/run_draft_reminders.py [--hours 48] [--limit 50]
"""
import sys
import logging
import argparse

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("draft_reminders_cli")

from app.core.database import init_connection_pool
from app.api.drafts import process_draft_reminders

def main():
    parser = argparse.ArgumentParser(description="Process NIWI incomplete draft reminders")
    parser.add_argument("--hours", type=int, default=None, help="Inactivity threshold in hours (default: 48 or DRAFT_REMINDER_HOURS env)")
    parser.add_argument("--limit", type=int, default=50, help="Max reminders to dispatch per run")
    args = parser.parse_args()

    try:
        init_connection_pool(minconn=1, maxconn=2)
    except Exception as e:
        logger.warning("Could not pre-init DB pool: %s", e)

    count = process_draft_reminders(limit=args.limit, hours_threshold=args.hours)
    logger.info("Draft reminder process complete. Sent: %d", count)
    print(f"Sent {count} draft reminder(s).")

if __name__ == "__main__":
    main()
