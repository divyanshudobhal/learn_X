import sqlite3

DB_NAME = "learnx.db"

def get_connection():
    return sqlite3.connect(DB_NAME, check_same_thread=False)

def init_db():
    conn = get_connection()
    cur = conn.cursor()

    # USERS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    # FILE UPLOADS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS uploads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uploaded_by TEXT,
            filename TEXT,
            url TEXT,
            tags TEXT,
            summary TEXT
        )
    """)

    # AI LOGS TABLE
    cur.execute("""
        CREATE TABLE IF NOT EXISTS ai_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question TEXT,
            answer TEXT,
            username TEXT
        )
    """)

    conn.commit()
    conn.close()

# Automatically create DB on import
init_db()
