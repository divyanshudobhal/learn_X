# db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

# Example: postgres://user:pass@host:port/dbname
DATABASE_URL = os.getenv("DATABASE_URL")


def get_db_connection():
    """Get a new DB connection."""
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is not set in environment variables.")
    return psycopg2.connect(DATABASE_URL)


def init_db():
    """Create tables if they don't exist."""
    conn = get_db_connection()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # UPLOADS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id SERIAL PRIMARY KEY,
            uploaded_by TEXT NOT NULL,
            filename TEXT NOT NULL,
            url TEXT NOT NULL,
            tags TEXT,
            summary TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # AI LOGS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_logs (
            id SERIAL PRIMARY KEY,
            username TEXT NOT NULL,
            question TEXT NOT NULL,
            answer TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)

    conn.commit()
    cur.close()
    conn.close()
