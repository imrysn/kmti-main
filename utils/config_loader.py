import json
import os
from pathlib import Path

CONFIG_FILE = "data/config.json"

def get_base_dir():
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, "r") as f:
                data = json.load(f)
                path = data.get("base_dir", "")
                if path and os.path.exists(path):
                    return Path(path)
        except:
            pass
    # fallback: default path
    return Path(r"X:\PROJECTS")
