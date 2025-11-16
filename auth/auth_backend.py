# auth/auth_backend.py
import hashlib
from psycopg2.extras import RealDictCursor
from db import get_db_connection


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def signup_user(username: str, password: str, role: str):
    """Create a new user in DB."""
    username = username.strip()
    role = role.strip()

    if not username or not password or not role:
        return False, "All fields are required."

    conn = get_db_connection()
    cur = conn.cursor()

    # Check if username exists
    cur.execute("SELECT 1 FROM users WHERE username = %s;", (username,))
    if cur.fetchone():
        cur.close()
        conn.close()
        return False, "❌ Username already exists!"

    pwd_hash = hash_password(password)

    cur.execute(
        "INSERT INTO users (username, password_hash, role) VALUES (%s, %s, %s);",
        (username, pwd_hash, role)
    )
    conn.commit()
    cur.close()
    conn.close()

    return True, f"✅ Signup successful! You are registered as {role}."


def login_user(username: str, password: str):
    """Verify username/password and return user object."""
    username = username.strip()

    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("SELECT id, username, password_hash, role FROM users WHERE username = %s;", (username,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return False, "❌ User not found!", None

    if row["password_hash"] != hash_password(password):
        return False, "⚠️ Incorrect password!", None

    user_info = {
        "id": row["id"],
        "username": row["username"],
        "role": row["role"]
    }
    return True, "Login successful!", user_info


def load_users():
    """Return all users (for Admin dashboard)."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, username, role, created_at FROM users ORDER BY created_at DESC;")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows
