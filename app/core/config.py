"""
config.py — Application configuration
Reads environment variables for DB, ACS, and app settings.
"""
import os

PGHOST       = os.environ.get("PGHOST", "localhost")
PGPORT       = os.environ.get("PGPORT", "5432")
PGDATABASE   = os.environ.get("PGDATABASE", "nd_audit")
PGUSER       = os.environ.get("PGUSER", "postgres")
PGPASSWORD   = os.environ.get("PGPASSWORD", "")

ACS_CONNECTION_STRING = os.environ.get("ACS_CONNECTION_STRING", "")
ACS_SENDER_ADDRESS    = os.environ.get("ACS_SENDER_ADDRESS", "")
