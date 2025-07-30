import json
import os
from datetime import datetime

LOG_FILE = "data/logs/activity_metadata.json"
USERS_FILE = "data/users.json"


def get_fullname(username: str) -> str:
    """
    Get fullname from users.json using username.
    If not found, return username.
    """
    if not os.path.exists(USERS_FILE):
        return username
    try:
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        for email, data in users.items():
            if data.get("username") == username:
                return data.get("fullname", username)
    except Exception:
        pass
    return username


def log_login(username: str, role: str):
    """
    Record a login entry for a user with login_time and fullname.
    """
    os.makedirs("data/logs", exist_ok=True)

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    now = datetime.now()
    entry = {
        "username": username,
        "fullname": get_fullname(username),
        "role": role,
        "login_time": now.strftime("%Y-%m-%d %H:%M:%S"),
        "logout_time": None,
        "runtime": None,
        "date": now.strftime("%Y-%m-%d")
    }
    logs.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)


def log_logout(username: str, role: str):
    """
    Updates the last login record of the user with logout_time and runtime.
    """
    os.makedirs("data/logs", exist_ok=True)

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    # Find the latest login for this username and role that has no logout_time
    for record in reversed(logs):
        if record["username"] == username and record["role"] == role and record["logout_time"] is None:
            logout_time = datetime.now()
            record["logout_time"] = logout_time.strftime("%Y-%m-%d %H:%M:%S")

            # Calculate runtime
            login_dt = datetime.strptime(record["login_time"], "%Y-%m-%d %H:%M:%S")
            delta = logout_time - login_dt
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            record["runtime"] = f"{hours:02}:{minutes:02}:{seconds:02}"
            break

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)
