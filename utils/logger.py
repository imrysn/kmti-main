import json
from datetime import datetime
import os

LOG_FILE = "data/logs/activity.log"
# Use the same file as session_logger to avoid redundancy
METADATA_FILE = "data/logs/activity_logs.json"
USERS_FILE = "data/users.json"


def _get_user_details(username: str):
    """Look up email, fullname, and role from users.json using username."""
    if not os.path.exists(USERS_FILE):
        return {"fullname": username, "email": "", "role": ""}

    with open(USERS_FILE, "r") as f:
        users = json.load(f)

    for email, data in users.items():
        if data.get("username") == username:
            return {
                "fullname": data.get("fullname", username),
                "email": email,
                "role": data.get("role", "")
            }
    return {"fullname": username, "email": "", "role": ""}


def log_action(username: str, activity: str):
    """
    Logs activity to both:
    - A plain text log file (activity.log)
    - A unified JSON metadata file (activity_logs.json)
    """
    details = _get_user_details(username)
    log_line = (
        f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')} - "
        f"{details['fullname']} ({details['email']}, {details['role']}) - {activity}\n"
    )

    # Plain text log
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(log_line)

    # Save to structured JSON file
    meta_entry = {
        "username": username,
        "fullname": details["fullname"],
        "email": details["email"],
        "role": details["role"],
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "activity": activity,
    }

    meta_data = []
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r") as f:
            try:
                meta_data = json.load(f)
            except json.JSONDecodeError:
                meta_data = []

    meta_data.append(meta_entry)
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, "w") as f:
        json.dump(meta_data, f, indent=4)
