import flet as ft
import json
import os
from login_window import login_view
from admin_panel import admin_panel
from user.user_panel import user_panel

SESSION_FILE = "data/session.json"

def restore_session(page: ft.Page):
    """Check for an existing session and open the appropriate panel."""
    if os.path.exists(SESSION_FILE):
        try:
            with open(SESSION_FILE, "r") as f:
                session = json.load(f)
            username = session.get("username")
            role = session.get("role", "user")
            if username:
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

    # Attempt session restore
    if not restore_session(page):
        login_view(page)

    page.update()

ft.app(
    target=main,
    assets_dir="assets",
    view=ft.AppView.FLET_APP
)
