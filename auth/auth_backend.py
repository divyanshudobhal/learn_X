import json
import os
import hashlib
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
USERS_FILE = os.path.join(BASE_DIR, "users.json")


def load_users():
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)
        return {}
    try:
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return {}

def save_users(users):
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
    return True, f"✅ Signup successful! Registered as {role}."

def login_user(username, password):
    users = load_users()

    if username not in users:
        return False, "❌ User not found!", None

    if users[username]["password"] != hash_password(password):
        return False, "⚠️ Incorrect password!", None

    return True, "Login successful!", {
        "username": username,
        "role": users[username]["role"]
    }
