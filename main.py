import flet as ft
import json
import os
from login_window import login_view
from admin_panel import admin_panel
from user.user_panel import user_panel
from typing import Optional
from datetime import datetime

# Paths
DATA_DIR = "data"
OLD_SESSION_FILE = os.path.join(DATA_DIR, "session.json")   # legacy single session
SESSIONS_DIR = os.path.join(DATA_DIR, "sessions")
REMEMBER_ME_FILE = os.path.join(DATA_DIR, "remember_me.json")


def migrate_old_session():
    """
    If the legacy data/session.json exists, migrate it to data/sessions/<username>.json
    then delete the old file. Safe to call repeatedly.
    """
    try:
        if not os.path.exists(OLD_SESSION_FILE):
            return
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        with open(OLD_SESSION_FILE, "r", encoding="utf-8") as f:
            old = json.load(f)
        username = old.get("username")
        if username:
            new_path = os.path.join(SESSIONS_DIR, f"{username}.json")
            with open(new_path, "w", encoding="utf-8") as nf:
                json.dump(old, nf, indent=4)
        # remove old legacy file after migration
        os.remove(OLD_SESSION_FILE)
    except Exception as e:
        print(f"[WARN] Failed to migrate old session: {e}")


def load_remembered_username() -> Optional[str]:
    """Return a remembered/last username from remember_me.json if available."""
    try:
        if not os.path.exists(REMEMBER_ME_FILE):
            return None
        with open(REMEMBER_ME_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        # if format is {username: {...}}, prefer a stored last_username key if present
        if isinstance(data, dict):
            if data.get("_last_username"):
                return data.get("_last_username")
            # if there's only one remembered username, return it
            keys = [k for k in data.keys() if not k.startswith("_")]
            if len(keys) == 1:
                return keys[0]
    except Exception as e:
        print(f"[DEBUG] Failed to read remember_me.json: {e}")
    return None


def choose_session_file():
    """
    Decide which session file to try to restore:
    1. If remember_me contains a username, prefer that.
    2. Else if there's only one file in data/sessions, choose it.
    3. Else pick the most recently modified session file.
    Returns path or None.
    """
    try:
        os.makedirs(SESSIONS_DIR, exist_ok=True)
        files = [
            os.path.join(SESSIONS_DIR, f) for f in os.listdir(SESSIONS_DIR)
            if f.endswith(".json")
        ]
        if not files:
            return None

        remembered = load_remembered_username()
        if remembered:
            candidate = os.path.join(SESSIONS_DIR, f"{remembered}.json")
            if os.path.exists(candidate):
                return candidate

        if len(files) == 1:
            return files[0]

        # pick by most recent modification time
        files.sort(key=lambda p: os.path.getmtime(p), reverse=True)
        return files[0]
    except Exception as e:
        print(f"[DEBUG] Failed to choose session file: {e}")
        return None


def restore_session(page: ft.Page) -> bool:
    """Check for an existing per-user session and open the appropriate panel."""
    try:
        migrate_old_session()

        session_path = choose_session_file()
        if not session_path:
            return False

        with open(session_path, "r", encoding="utf-8") as f:
            session = json.load(f)

        username = session.get("username")
        role = session.get("role", "user")
        if not username:
            return False

        # Route to appropriate panel
        if role.upper() == "ADMIN":
            admin_panel(page, username)
            return True
        else:
            user_panel(page, username)
            return True
    except Exception as e:
        print(f"[DEBUG] Failed to restore session: {e}")
        return False


def main(page: ft.Page):
    # Set window properties first
    page.title = "KMTI Data Management System"
    page.window_icon = "assets/kmti.ico"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Ensure data directories exist
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    # Attempt session restore
    if not restore_session(page):
        login_view(page)

    page.update()


if __name__ == "__main__":
    ft.app(
        target=main,
        assets_dir="assets",
        view=ft.AppView.FLET_APP
    )
