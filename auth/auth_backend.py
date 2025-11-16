# auth/auth_backend.py
import hashlib
from db import get_db_connection
from psycopg2.extras import RealDictCursor


# -----------------------------
# Password Hashing
# -----------------------------
def hash_password(password: str) -> str:
    """Encrypt password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


# -----------------------------
# Load Users (for admin dashboard)
# -----------------------------
def load_users():
    """
    Returns a list of users as dicts:
      [{id, username, role, created_at}, ...]
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("SELECT id, username, role, created_at FROM users ORDER BY id;")
    users = cur.fetchall()
    cur.close()
    conn.close()
    return users


# -----------------------------
# Signup Logic
# -----------------------------
def signup_user(username, password, role):
    """Register a new user in PostgreSQL."""
    conn = get_db_connection()
    cur = conn.cursor()

    try:
        # Check if username exists
        cur.execute("SELECT 1 FROM users WHERE username = %s;", (username,))
        if cur.fetchone():
            return False, "❌ Username already exists!"

        # Insert new user
        cur.execute(
            "INSERT INTO users (username, password, role) VALUES (%s, %s, %s);",
            (username, hash_password(password), role)
        )
        conn.commit()
        return True, f"✅ Signup successful! You are registered as {role}."

    except Exception as e:
        conn.rollback()
        return False, f"Error while signing up: {e}"

    finally:
        cur.close()
        conn.close()


# -----------------------------
# Login Logic
# -----------------------------
def login_user(username, password):
    """
    Authenticate user from PostgreSQL.
    Returns: (success: bool, msg: str, user_info: dict|None)
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    try:
        cur.execute(
            "SELECT username, password, role FROM users WHERE username = %s;",
            (username,)
        )
        user = cur.fetchone()

        if not user:
            return False, "❌ User not found!", None

        if user["password"] != hash_password(password):
            return False, "⚠️ Incorrect password!", None

        user_info = {
            "username": user["username"],
            "role": user["role"]
        }
        return True, "Login successful!", user_info

    except Exception as e:
        return False, f"Login error: {e}", None

    finally:
        cur.close()
        conn.close()
