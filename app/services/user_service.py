import psycopg2.extras

def verify_user(conn, email: str) -> dict:
    """Check if an email exists in admin_users and return role."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT email, role FROM admin_users WHERE email = %s", (email,))
        row = cur.fetchone()
        
    if row:
        return {"authorized": True, "role": row["role"]}
    return {"authorized": False}

def get_users(conn) -> list:
    """Get all admin users."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute("SELECT id, email, role, created_at FROM admin_users ORDER BY created_at DESC")
        return cur.fetchall()

def add_user(conn, email: str, role: str) -> dict:
    """Add a new user."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        try:
            cur.execute(
                "INSERT INTO admin_users (email, role) VALUES (%s, %s) RETURNING id, email, role, created_at",
                (email, role)
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row)
        except psycopg2.IntegrityError:
            conn.rollback()
            # If exists, update role instead
            cur.execute(
                "UPDATE admin_users SET role = %s WHERE email = %s RETURNING id, email, role, created_at",
                (role, email)
            )
            row = cur.fetchone()
            conn.commit()
            return dict(row)

def remove_user(conn, email: str) -> bool:
    """Remove a user."""
    with conn.cursor() as cur:
        cur.execute("DELETE FROM admin_users WHERE email = %s", (email,))
        deleted = cur.rowcount > 0
    conn.commit()
    return deleted
