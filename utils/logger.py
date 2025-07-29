import json
import os
from datetime import datetime

LOG_FILE = "data/logs/activity_logs.json"


def log_action(username: str, action: str, role: str = None):
    """
    Records a simple activity entry.
    Only stores activity details (not runtime, login_time, or logout_time).
    """
    os.makedirs("data/logs", exist_ok=True)

    logs = []
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            try:
                logs = json.load(f)
            except json.JSONDecodeError:
                logs = []

    entry = {
        "username": username,
        "role": role if role else "unknown",
        "activity": action,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

    logs.append(entry)

    with open(LOG_FILE, "w") as f:
        json.dump(logs, f, indent=4)
