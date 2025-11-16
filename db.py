# db.py
import os
import psycopg2
from psycopg2.extras import RealDictCursor

def get_db_connection():
    """
    Returns a new connection to PostgreSQL using Railway / Render env vars.
    Make sure these are set:
      PGHOST, PGPORT, PGDATABASE, PGUSER, PGPASSWORD
    """
    conn = psycopg2.connect(
        host=os.getenv("PGHOST"),
        port=os.getenv("PGPORT", "5432"),
        dbname=os.getenv("PGDATABASE"),
        user=os.getenv("PGUSER"),
        password=os.getenv("PGPASSWORD")
    )
    return conn


def init_db():
    """
    Create tables if they don't exist.
    Run once at app startup (we call this from app.py).
    """
    conn = get_db_connection()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
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
            tags TEXT,                 -- comma-separated tags
            summary TEXT,
            uploaded_at TIMESTAMP DEFAULT NOW()
        );
    """)

    # AI_LOGS TABLE
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
