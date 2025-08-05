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
    # ===== FULLSCREEN CONFIGURATION =====
    page.title = "KMTI Data Management System"
    page.window_icon = "assets/kmti.ico"
    page.theme_mode = ft.ThemeMode.LIGHT
    
    # FULLSCREEN SETTINGS
    page.window_maximized = True  # Start maximized
    page.window_maximizable = True  # Allow maximize/restore
    page.window_resizable = True  # Allow resizing
    page.window_full_screen = False  # Don't force full screen (allows window controls)
    
    # Window size fallback if maximized doesn't work
    page.window_width = 1200
    page.window_height = 800
    page.window_min_width = 800
    page.window_min_height = 600
    
    # Padding and spacing optimizations for fullscreen
    page.padding = 0
    page.spacing = 0
    
    # ===== KEYBOARD SHORTCUTS FOR FULLSCREEN TOGGLE =====
    def handle_keyboard(e: ft.KeyboardEvent):
        # F11 to toggle fullscreen
        if e.key == "F11":
            page.window_full_screen = not page.window_full_screen
            page.update()
        # Ctrl+M to toggle maximized
        elif e.key == "M" and e.ctrl:
            page.window_maximized = not page.window_maximized
            page.update()
    
    page.on_keyboard_event = handle_keyboard

    # ===== SESSION RESTORATION =====
    # Attempt session restore
    if not restore_session(page):
        login_view(page)

    page.update()

ft.app(
    target=main,
    assets_dir="assets",
    view=ft.AppView.FLET_APP
)   