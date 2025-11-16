import json
import os
import hashlib

# -----------------------------
# Base directory for JSON
# -----------------------------
# In Railway it will be /data (from env DATA_DIR)
BASE_DIR = os.getenv(
    "DATA_DIR",
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # local fallback
)

USERS_FILE = os.path.join(BASE_DIR, "users.json")


def load_users():
    """Load users safely from JSON."""
    if not os.path.exists(USERS_FILE):
        # create empty JSON file if not exists
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
        return {}

    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}


def save_users(users):
    """Save users to JSON."""
    # ensure directory exists
    os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
    with open(USERS_FILE, "w") as f:
        json.dump(users, f, indent=4)


def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()


def signup_user(username, password, role):
    users = load_users()

    if username in users:
        return False, "❌ Username already exists!"

    users[username] = {
        "password": hash_password(password),
        "role": role
    }

    save_users(users)
    return True, f"✅ Signup successful! You are registered as {role}."


def login_user(username, password):
    users = load_users()

    if username not in users:
        return False, "❌ User not found!", None

    stored_hash = users[username]["password"]
    if stored_hash != hash_password(password):
        return False, "⚠️ Incorrect password!", None

    user_info = {
        "username": username,
        "role": users[username]["role"]
    }
    return True, "Login successful!", user_info
