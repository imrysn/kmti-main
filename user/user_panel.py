import flet as ft
import os
import json
from typing import Optional
from datetime import datetime

from .components.browser_view import BrowserView
from .components.profile_view import ProfileView
from .components.files_view import FilesView
from .components.approval_files_view import ApprovalFilesView
from .components.notifications_view import NotificationsView
from .services.profile_service import ProfileService
from .services.file_service import FileService
from .services.approval_file_service import ApprovalFileService
from utils.logger import log_action
from utils.session_logger import log_activity

SESSION_BASE_DIR = os.path.join("session")  # central session folder


def safe_username_for_file(username: str) -> str:
    """Return a filename-safe username."""
    return "".join(c for c in (username or "") if c.isalnum() or c in ("-", "_")).strip() or "user"


def save_session(username: str, role: str):
    """Save the current session for a user."""
    safe_name = safe_username_for_file(username)
    user_dir = os.path.join(SESSION_BASE_DIR, safe_name)
    os.makedirs(user_dir, exist_ok=True)
    session_data = {
        "username": username,
        "role": role,
        "last_login": datetime.now().isoformat()
    }
    with open(os.path.join(user_dir, "session.json"), "w") as f:
        json.dump(session_data, f, indent=4)
    print(f"[DEBUG] Session saved for {username} at {user_dir}")


def load_session(username: str) -> Optional[dict]:
    """Load session data for a given user."""
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_BASE_DIR, safe_name, "session.json")
    if os.path.exists(session_file):
        with open(session_file, "r") as f:
            return json.load(f)
    return None


def clear_session(username: str):
    """Remove only this user's session file."""
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_BASE_DIR, safe_name, "session.json")
    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"[DEBUG] Removed session file {session_file}")


def user_panel(page: ft.Page, username: Optional[str]):
    if not username:
        from login_window import login_view
        login_view(page)
        return

    # Save persistent session
    save_session(username, "user")

    user_folder = f"data/uploads/{username}"
    os.makedirs(user_folder, exist_ok=True)

    profile_service = ProfileService(user_folder, username)
    file_service = FileService(user_folder, username)
    approval_service = ApprovalFileService(user_folder, username)

    browser_view = BrowserView(page, username)
    profile_view = ProfileView(page, username, profile_service)
    files_view = FilesView(page, username, file_service)
    approval_files_view = ApprovalFilesView(page, username, approval_service)
    notifications_view = NotificationsView(page, username, approval_service)

    current_view = "browser"

    log_action(username, "Login")
    log_activity(username, "Login")

    def logout(e):
        log_action(username, "Logout")
        log_activity(username, "Logout")
        clear_session(username)
        page.controls.clear()
        page.appbar = None
        page.overlay.clear()
        page.title = "Login"
        page.bgcolor = None
        page.update()
        from login_window import login_view
        login_view(page)

    def show_profile_view(): 
        nonlocal current_view
        current_view = "profile"
        update_content()

    def show_files_view(): 
        nonlocal current_view
        current_view = "files"
        update_content()

    def show_approval_files_view(): 
        nonlocal current_view
        current_view = "approval_files"
        update_content()

    def show_notifications_view(): 
        nonlocal current_view
        current_view = "notifications"
        update_content()

    def show_browser_view(): 
        nonlocal current_view
        current_view = "browser"
        update_content()

    navigation = {
        'show_profile': show_profile_view,
        'show_files': show_files_view,
        'show_approval_files': show_approval_files_view,
        'show_notifications': show_notifications_view,
        'show_browser': show_browser_view
    }

    browser_view.set_navigation(navigation)
    profile_view.set_navigation(navigation)
    files_view.set_navigation(navigation)
    approval_files_view.set_navigation(navigation)
    notifications_view.set_navigation(navigation)

    def get_notification_status():
        try:
            unread_count = approval_service.get_unread_notification_count()
            if unread_count > 0:
                return f"({unread_count})", ft.Icons.NOTIFICATIONS_ACTIVE
            else:
                return "", ft.Icons.NOTIFICATIONS_NONE
        except:
            return "", ft.Icons.NOTIFICATIONS_NONE

    def update_content():
        print(f"[DEBUG] Updating content: {current_view}")
        try:
            if current_view == "profile":
                content = profile_view.create_content()
            elif current_view == "files":
                content = files_view.create_content()
            elif current_view == "approval_files":
                content = approval_files_view.create_content()
            elif current_view == "notifications":
                content = notifications_view.create_content()
            else:
                content = browser_view.create_content()

            page.controls.clear()
            notification_badge, notification_icon = get_notification_status()

            page.appbar = ft.AppBar(
                title=ft.Text("User Dashboard", color=ft.Colors.WHITE),
                actions=[
                    ft.IconButton(
                        icon=notification_icon,
                        icon_color=ft.Colors.WHITE,
                        tooltip="Notifications",
                        on_click=lambda e: show_notifications_view()
                    ),
                    ft.TextButton(
                        f"Hi, {username}" if username else "Hi, User",
                        style=ft.ButtonStyle(color=ft.Colors.WHITE),
                        on_click=lambda e: show_profile_view()
                    ),
                    ft.TextButton(
                        "Logout",
                        style=ft.ButtonStyle(color=ft.Colors.WHITE),
                        on_click=logout
                    )
                ],
                bgcolor=ft.Colors.GREY_800
            )
            page.add(content)
            page.update()
            print("[DEBUG] Content added and page updated.")
        except Exception as e:
            print(f"[ERROR] Failed to update content: {e}")
            page.controls.clear()
            page.add(ft.Text(f"An error occurred: {e}", color=ft.Colors.RED))
            page.update()

    page.title = "KMTI Data Management Users"
    page.bgcolor = ft.Colors.GREY_200
    update_content()
