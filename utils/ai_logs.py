import os
import json

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AI_LOGS_FILE = os.path.join(BASE_DIR, "../ai_logs.json")   # FIXED PATH

def load_ai_logs():
    """Load AI logs safely."""
    if not os.path.exists(AI_LOGS_FILE):
        return []

    try:
        with open(AI_LOGS_FILE, "r") as f:
            return json.load(f)
    except:
        return []


def save_ai_log(question, answer, username):
    """Save a new AI log entry."""
    logs = load_ai_logs()

    logs.append({
        "user": username,
        "question": question,
        "answer": answer
    })

    with open(AI_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)
