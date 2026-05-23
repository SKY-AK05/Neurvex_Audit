import asyncio
import json
from datetime import datetime, timedelta
import logging

from app.core.database import get_conn
from app.services.settings_service import send_acs_email

logger = logging.getLogger(__name__)

async def process_dlq_loop():
    while True:
        try:
            conn = get_conn()
            with conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT * FROM email_dlq WHERE status = 'pending' AND next_retry_at <= NOW()")
                    rows = cur.fetchall()
                    
                    for row in rows:
                        import psycopg2.extras
                        # row is a tuple since we didn't use RealDictCursor here, let's fix it
                        pass
            conn.close()
        except Exception as e:
            logger.error(f"DLQ processor error: {e}")
            
        await asyncio.sleep(60)

async def start_dlq_worker():
    asyncio.create_task(run_dlq_worker())

async def run_dlq_worker():
    while True:
        try:
            import psycopg2.extras
            conn = get_conn()
            with conn:
                with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                    cur.execute("SELECT * FROM email_dlq WHERE status = 'pending' AND next_retry_at <= NOW()")
                    rows = cur.fetchall()
                    
                    for row in rows:
                        payload = row['payload']
                        if isinstance(payload, str):
                            payload = json.loads(payload)
                            
                        try:
                            # Send email
                            send_acs_email(**payload)
                            
                            # Update DLQ success
                            cur.execute("UPDATE email_dlq SET status = 'sent' WHERE id = %s", (row['id'],))
                            # Update submission
                            cur.execute("UPDATE submissions SET status = 'sent', sent_at = NOW() WHERE id = %s", (row['submission_id'],))
                        except Exception as e:
                            next_retry = datetime.now() + timedelta(minutes=15)
                            cur.execute(
                                "UPDATE email_dlq SET attempts = attempts + 1, last_error = %s, next_retry_at = %s WHERE id = %s", 
                                (str(e), next_retry, row['id'])
                            )
                            # If attempts > 5, mark as failed permanently
                            if row['attempts'] >= 5:
                                cur.execute("UPDATE email_dlq SET status = 'failed' WHERE id = %s", (row['id'],))
                                cur.execute("UPDATE submissions SET status = 'failed' WHERE id = %s", (row['submission_id'],))
            conn.close()
        except Exception as e:
            logger.error(f"DLQ processor error: {e}")
            
        await asyncio.sleep(60)
