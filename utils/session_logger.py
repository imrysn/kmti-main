import json
import os
from datetime import datetime

LOG_FILE = "data/logs/activity_logs.json"
USERS_FILE = "data/users.json"


def ensure_log_file():
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    if not os.path.exists(LOG_FILE):
        with open(LOG_FILE, "w") as f:
            json.dump([], f)


def load_user_details(username: str):
    """Load fullname, email, and role from users.json based on username."""
    if not os.path.exists(USERS_FILE):
        return username, username, "", ""
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        for email, data in users.items():
            if data.get("username") == username:
                return (
                    data.get("username", username),
                    data.get("fullname", username),
                    email,
                    data.get("role", ""),
                )
    except Exception:
        pass
    return username, username, "", ""


def log_action(username: str, description: str):
    """Generic log entry writer that records description."""
    ensure_log_file()
    _, fullname, email, role = load_user_details(username)

    with open(LOG_FILE, "r") as f:
        logs = json.load(f)

    logs.append({
        "username": username,
        "fullname": fullname,
        "email": email,
        "role": role.upper(),
        "datetime": datetime.now().isoformat(),
        "description": description
    })

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)


def log_login(username: str, role: str):
    """Log when a user logs in."""
    log_action(username, f"Logged into {role} panel")
