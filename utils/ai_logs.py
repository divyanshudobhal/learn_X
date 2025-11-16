import json
import os

# Base dir for logs (DATA_DIR on Railway)
BASE_DIR = os.getenv(
    "DATA_DIR",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # local fallback
)

AI_LOGS_FILE = os.path.join(BASE_DIR, "ai_logs.json")


def load_ai_logs():
    if not os.path.exists(AI_LOGS_FILE):
        return []
    with open(AI_LOGS_FILE, "r") as f:
        return json.load(f)


def save_ai_logs(logs):
    os.makedirs(os.path.dirname(AI_LOGS_FILE), exist_ok=True)
    with open(AI_LOGS_FILE, "w") as f:
        json.dump(logs, f, indent=4)


def save_ai_log(question, answer, username):
    logs = load_ai_logs()
    logs.append({
        "user": username,
        "question": question,
        "answer": answer
    })
    save_ai_logs(logs)

