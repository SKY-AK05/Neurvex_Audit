"""
user_service.py — Administrator user management services
Enforces role validation ('admin', 'super') and prevents accidental deletion or demotion of the last Super Admin.
"""
import psycopg2.extras
from fastapi import HTTPException

VALID_ROLES = {"admin", "super"}

def verify_user(conn, email: str) -> dict:
    """Check if an email exists in admin_users and return role."""
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
            (email.strip(),),
        )
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
    """
    Add a new administrator or update an existing administrator's role.
    Validates role and ensures the last Super Admin cannot be demoted.
    """
    email_clean = email.strip().lower()
    role_clean = role.strip().lower()
    
    if role_clean not in VALID_ROLES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid role '{role}'. Allowed roles are: {', '.join(sorted(VALID_ROLES))}"
        )
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        # Check if user already exists
        cur.execute(
            "SELECT id, email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
            (email_clean,)
        )
        existing = cur.fetchone()
        
        # If user is currently a super admin and being demoted to admin
        if existing and existing["role"] == "super" and role_clean != "super":
            cur.execute("SELECT COUNT(*) as count FROM admin_users WHERE role = 'super'")
            super_count = cur.fetchone()["count"]
            if super_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot demote the last remaining Super Admin. At least one Super Admin must exist."
                )
        
        if existing:
            cur.execute(
                "UPDATE admin_users SET role = %s WHERE LOWER(email) = LOWER(%s) RETURNING id, email, role, created_at",
                (role_clean, email_clean)
            )
            row = cur.fetchone()
        else:
            cur.execute(
                "INSERT INTO admin_users (email, role) VALUES (%s, %s) RETURNING id, email, role, created_at",
                (email_clean, role_clean)
            )
            row = cur.fetchone()
            
        conn.commit()
        return dict(row)


def remove_user(conn, email: str) -> bool:
    """
    Remove an administrator user.
    Prevents deletion of the last remaining Super Admin.
    """
    email_clean = email.strip().lower()
    
    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
        cur.execute(
            "SELECT id, email, role FROM admin_users WHERE LOWER(email) = LOWER(%s)",
            (email_clean,)
        )
        user = cur.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        if user["role"] == "super":
            cur.execute("SELECT COUNT(*) as count FROM admin_users WHERE role = 'super'")
            super_count = cur.fetchone()["count"]
            if super_count <= 1:
                raise HTTPException(
                    status_code=400,
                    detail="Cannot delete the last remaining Super Admin. At least one Super Admin must exist."
                )
        
        cur.execute("DELETE FROM admin_users WHERE LOWER(email) = LOWER(%s)", (email_clean,))
        deleted = cur.rowcount > 0
        conn.commit()
        return deleted
