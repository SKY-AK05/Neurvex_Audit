"""
database.py — Database connection management
"""
import psycopg2
from app.core.config import PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD


def get_conn():
    return psycopg2.connect(
        host=PGHOST,
        port=PGPORT,
        dbname=PGDATABASE,
        user=PGUSER,
        password=PGPASSWORD,
        sslmode="require",
    )
