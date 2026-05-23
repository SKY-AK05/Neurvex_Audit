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

with open('migrations/005_rbac.sql', 'r') as f:
    sql = f.read()

with conn.cursor() as cur:
    cur.execute(sql)
    
conn.commit()
conn.close()
print("Migration applied successfully.")
