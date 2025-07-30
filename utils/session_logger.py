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


def _load_logs():
    """Load log records safely."""
    if not os.path.exists(LOG_FILE):
        return []
    try:
        with open(LOG_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, FileNotFoundError):
        return []


def _save_logs(logs):
    """Save log records safely."""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)


def log_login(username: str, role: str):
    """
    Record a login entry for a user with login_time and fullname.
    If the user already has an open session (no logout_time), close it before adding new login.
    """
    logs = _load_logs()
    role = role.upper()

    # Close previous unfinished session for this user/role
    for record in reversed(logs):
        if record["username"] == username and record["role"].upper() == role and record["logout_time"] is None:
            logout_time = datetime.now()
            record["logout_time"] = logout_time.strftime("%Y-%m-%d %H:%M:%S")
            login_dt = datetime.strptime(record["login_time"], "%Y-%m-%d %H:%M:%S")
            delta = logout_time - login_dt
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            record["runtime"] = f"{hours:02}:{minutes:02}:{seconds:02}"
            break

    # Create new login session
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
    _save_logs(logs)


def log_logout(username: str, role: str):
    """
    Updates the last login record of the user with logout_time and runtime.
    """
    logs = _load_logs()
    role = role.upper()

    for record in reversed(logs):
        if record["username"] == username and record["role"].upper() == role and record["logout_time"] is None:
            logout_time = datetime.now()
            record["logout_time"] = logout_time.strftime("%Y-%m-%d %H:%M:%S")
            login_dt = datetime.strptime(record["login_time"], "%Y-%m-%d %H:%M:%S")
            delta = logout_time - login_dt
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            record["runtime"] = f"{hours:02}:{minutes:02}:{seconds:02}"
            break

    _save_logs(logs)


def get_active_sessions():
    """
    Returns a dictionary of currently logged-in users (no logout_time).
    Structure:
    {
        "username:ROLE": {
            "username": "...",
            "role": "...",
            "login_time": "...",
            "fullname": "..."
        }
    }
    """
    logs = _load_logs()
    active = {}

    for record in logs:
        # Only consider truly active sessions
        if record.get("logout_time") is None:
            uname = record["username"]
            role = record["role"].upper()
            key = f"{uname}:{role}"
            # Store only the latest open session
            active[key] = {
                "username": uname,
                "role": role,
                "login_time": record["login_time"],
                "fullname": record.get("fullname", uname),
            }

    return active


def get_last_runtime(username: str) -> str:
    """
    Return the runtime from the last completed session (where logout_time is set).
    If the latest session is active, return "-".
    """
    logs = _load_logs()
    user_entries = [entry for entry in logs if entry.get("username") == username]

    if not user_entries:
        return "-"

    # Sort latest first
    user_entries.sort(key=lambda x: x.get("login_time", ""), reverse=True)
    last = user_entries[0]

    if last.get("logout_time") is None:
        return "-"
    return last.get("runtime", "-")
