import flet as ft
import json
import os
from login_window import login_view
from admin_panel import admin_panel
from user.user_panel import user_panel
from typing import Optional
from datetime import datetime
from utils.path_config import DATA_PATHS

# Paths - now using centralized path configuration
DATA_DIR = DATA_PATHS.LOCAL_BASE  # Local data for sessions, logs, and local config
NETWORK_DATA_DIR = DATA_PATHS.NETWORK_BASE  # Network data directory
OLD_SESSION_FILE = os.path.join(DATA_DIR, "session.json")   # legacy single session
SESSIONS_DIR = DATA_PATHS.local_sessions_dir  # Keep sessions local

# Also check for the old session folder format and migrate if needed
OLD_SESSION_ROOT = os.path.join(DATA_DIR, "session")


def safe_username_for_file(username: str) -> str:
    """Return a filename-safe username."""
    return "".join(c for c in (username or "") if c.isalnum() or c in ("-", "_")).strip() or "user"

def migrate_old_session():
    """
    Migrate legacy sessions to the new format:
    1. data/session.json -> data/sessions/<username>.json
    2. data/session/<username>/session.json -> data/sessions/<username>.json
    Safe to call repeatedly.
    """
    try:
        # Migrate legacy single session file
        if os.path.exists(OLD_SESSION_FILE):
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            with open(OLD_SESSION_FILE, "r", encoding="utf-8") as f:
                old = json.load(f)
            username = old.get("username")
            if username:
                safe_name = safe_username_for_file(username)
                new_path = os.path.join(SESSIONS_DIR, f"{safe_name}.json")
                # Ensure it has the new format
                session_data = {
                    "username": username,
                    "role": old.get("role", "USER"),
                    "panel": "user" if old.get("role", "USER").upper() != "ADMIN" else "admin",
                    "login_time": old.get("login_time", datetime.now().isoformat())
                }
                with open(new_path, "w", encoding="utf-8") as nf:
                    json.dump(session_data, nf, indent=4)
            os.remove(OLD_SESSION_FILE)
            print(f"[DEBUG] Migrated legacy session file for {username}")
        
        # Migrate old session folder structure (data/session/<username>/session.json)
        if os.path.exists(OLD_SESSION_ROOT) and os.path.isdir(OLD_SESSION_ROOT):
            os.makedirs(SESSIONS_DIR, exist_ok=True)
            for user_folder in os.listdir(OLD_SESSION_ROOT):
                old_session_path = os.path.join(OLD_SESSION_ROOT, user_folder, "session.json")
                if os.path.exists(old_session_path):
                    with open(old_session_path, "r", encoding="utf-8") as f:
                        old_data = json.load(f)
                    username = old_data.get("username")
                    if username:
                        safe_name = safe_username_for_file(username)
                        new_path = os.path.join(SESSIONS_DIR, f"{safe_name}.json")
                        with open(new_path, "w", encoding="utf-8") as nf:
                            json.dump(old_data, nf, indent=4)
                        os.remove(old_session_path)
                        print(f"[DEBUG] Migrated session for {username} from old folder structure")
            
            # Clean up empty directories
            try:
                for user_folder in os.listdir(OLD_SESSION_ROOT):
                    folder_path = os.path.join(OLD_SESSION_ROOT, user_folder)
                    if os.path.isdir(folder_path) and not os.listdir(folder_path):
                        os.rmdir(folder_path)
                if not os.listdir(OLD_SESSION_ROOT):
                    os.rmdir(OLD_SESSION_ROOT)
            except:
                pass
                
    except Exception as e:
        print(f"[WARN] Failed to migrate old session: {e}")


def load_remembered_username() -> Optional[str]:
    """REMOVED: Remember Me feature disabled"""
    return None

def choose_session_file():
    """
    Decide which session file to try to restore:
    1. If there's only one file in data/sessions, choose it.
    2. Else pick the most recently modified session file.
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
        role = session.get("role", "USER").upper()
        if not username:
            return False

        # Route to appropriate panel based on role
        if role == "ADMIN":
            admin_panel(page, username)
            return True
        elif role == "TEAM_LEADER":
            from TLPanel import TLPanel
            TLPanel(page, username)
            return True
        elif role == "USER":
            user_panel(page, username)
            return True
        else:
            print(f"[WARNING] Unknown role: {role}, defaulting to user panel")
            user_panel(page, username)
            return True
    except Exception as e:
        print(f"[DEBUG] Failed to restore session: {e}")
        return False


def main(page: ft.Page):
    # Set window properties first
    page.title = "KMTI Data Management System"
    page.window_icon = "fms-icon.ico"
    page.theme_mode = ft.ThemeMode.LIGHT

    # Ensure data directories exist using centralized path management
    DATA_PATHS.ensure_local_dirs()
    if DATA_PATHS.is_network_available():
        DATA_PATHS.ensure_network_dirs()
    else:
        print(f"Warning: Network directory {NETWORK_DATA_DIR} is not accessible")

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
