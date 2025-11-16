# utils/ai_logs.py
from psycopg2.extras import RealDictCursor
from db import get_db_connection


def load_ai_logs():
    """Return all AI logs (latest first)."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    cur.execute("""
        SELECT id, username, question, answer, created_at
        FROM ai_logs
        ORDER BY created_at DESC;
    """)
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def save_ai_log(question: str, answer: str, username: str):
    """Insert one AI Q/A into DB."""
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO ai_logs (username, question, answer)
        VALUES (%s, %s, %s);
    """, (username, question, answer))
    conn.commit()
    cur.close()
    conn.close()
