import json
import os
from datetime import datetime

LOG_FILE = r"\\KMTI-NAS\Shared\data\logs\activity_metadata.json"
USERS_FILE = r"\\KMTI-NAS\Shared\data\users.json"
SESSION_ROOT = "/data/sessions"  


# --------------------------
# Session management helpers
# --------------------------

def save_session(username: str, session_data: dict):
    """
    Save session data in session/<username>/session.json.
    """
    user_session_dir = os.path.join(SESSION_ROOT, username)
    os.makedirs(user_session_dir, exist_ok=True)
    session_file = os.path.join(user_session_dir, "session.json")

    with open(session_file, "w") as f:
        json.dump(session_data, f, indent=4)


def load_session(username: str):
    """
    Load session for a given username.
    Returns dict if session exists, else None.
    """
    session_file = os.path.join(SESSION_ROOT, username, "session.json")
    if not os.path.exists(session_file):
        return None
    try:
        with open(session_file, "r") as f:
            return json.load(f)
    except Exception:
        return None


def clear_session(username: str):
    """
    Remove a user's session.json file.
    """
    session_file = os.path.join(SESSION_ROOT, username, "session.json")
    if os.path.exists(session_file):
        try:
            os.remove(session_file)
        except Exception:
            pass


# --------------------------
# Logging helpers
# --------------------------

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

    # Close any unfinished session for this user/role
    for record in reversed(logs):
        if record["username"] == username and record["role"] == role and record["logout_time"] is None:
            logout_time = datetime.now()
            record["logout_time"] = logout_time.strftime("%Y-%m-%d %H:%M:%S")
            # Compute runtime for that old session
            login_dt = datetime.strptime(record["login_time"], "%Y-%m-%d %H:%M:%S")
            delta = logout_time - login_dt
            total_seconds = int(delta.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            record["runtime"] = f"{hours:02}:{minutes:02}:{seconds:02}"
            break

    # Add a fresh login entry
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

    _save_logs(logs)


def get_active_sessions():
    """
    Returns a dictionary of currently logged-in users (no logout_time).
    Structure:
    {
        "username:role": {
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
        if record.get("logout_time") is None:
            uname = record["username"]
            role = record["role"]
            key = f"{uname}:{role}"
            active[key] = {
                "username": uname,
                "role": role,
                "login_time": record["login_time"],
                "fullname": record.get("fullname", uname),
            }

    return active


def get_last_runtime(username: str) -> str:
    """
    Get the last recorded runtime from activity_metadata.json for a logged-out user.
    """
    logs = _load_logs()
    for record in reversed(logs):
        if record["username"] == username and record.get("logout_time"):
            return record.get("runtime") or "-"
    return "-"


# --------------------------------------------------------------------
# Unified log_activity function for admin/user actions
# --------------------------------------------------------------------

def log_activity(username: str, description: str):
    """
    Record an admin/user action (not tied to login sessions).
    Format is unified with logger.py:
    - activity
    - date
    """
    log_file = r"\\KMTI-NAS\Shared\data\logs\activity_logs.json"

    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    # Load existing logs
    logs = []
    if os.path.exists(log_file):
        try:
            with open(log_file, "r") as f:
                logs = json.load(f)
        except Exception:
            logs = []

    entry = {
        "username": username,
        "fullname": get_fullname(username),
        "activity": description,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }

    logs.append(entry)

    with open(log_file, "w") as f:
        json.dump(logs, f, indent=4)


def log_panel_access(username: str, role: str, panel: str, login_type: str):
    """
    Log specific panel access for Team Leaders to track which panel they accessed.
    This helps with activity metadata tracking for dual access roles.
    """
    panel_description = {
        "user": "User Panel (file upload/management)",
        "admin": "Team Leader Panel (file review/approval)" if role == "TEAM_LEADER" else "Admin Panel"
    }.get(panel, f"{panel} Panel")
    
    login_method = "Admin Login" if login_type == "admin" else "User Login"
    
    description = f"Accessed {panel_description} via {login_method}"
    log_activity(username, description)
