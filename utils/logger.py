from datetime import datetime
import os

LOG_PATH = "data/logs/activity.log"
os.makedirs(os.path.dirname(LOG_PATH), exist_ok=True)

def log_action(user, action):
    with open(LOG_PATH, "a") as f:
        f.write(f"{datetime.now()} | {user} | {action}\n")
