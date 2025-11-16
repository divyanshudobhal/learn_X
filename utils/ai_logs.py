# utils/ai_logs.py
from db import get_db_connection
from psycopg2.extras import RealDictCursor


def load_ai_logs(limit: int = 100):
    """
    Return latest AI logs as a list of dicts for admin dashboard.
    """
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)

    cur.execute("""
        SELECT id, username, question, answer, created_at
        FROM ai_logs
        ORDER BY created_at DESC
        LIMIT %s;
    """, (limit,))
    logs = cur.fetchall()

    cur.close()
    conn.close()
    return logs


def save_ai_log(question: str, answer: str, username: str):
    """
    Insert a new AI interaction into ai_logs.
    """
    conn = get_db_connection()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO ai_logs (username, question, answer)
        VALUES (%s, %s, %s);
    """, (username, question, answer))

    conn.commit()
    cur.close()
    conn.close()
