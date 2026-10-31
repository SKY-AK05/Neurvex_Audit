import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.environ["PGHOST"],
    dbname=os.environ["PGDATABASE"],
    user=os.environ["PGUSER"],
    password=os.environ["PGPASSWORD"],
    port=os.environ.get("PGPORT", "5432"),
    sslmode="require",
)

with conn.cursor() as cur:
    cur.execute("SELECT column_name, data_type, is_nullable FROM information_schema.columns WHERE table_name = 'admin_users'")
    for row in cur.fetchall():
        print(row)
    
conn.close()
