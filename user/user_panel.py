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
from .components.notifications_window import NotificationsWindow  
from .services.profile_service import ProfileService
from .services.file_service import FileService
from .services.approval_file_service import ApprovalFileService
from utils.logger import log_action
from utils.session_logger import log_activity

SESSION_ROOT = r"\\KMTI-NAS\Shared\data\session"


def safe_username_for_file(username: str) -> str:
    """Return a filename-safe username."""
    return "".join(c for c in (username or "") if c.isalnum() or c in ("-", "_")).strip() or "user"


def save_session(username: str, role: str, panel: str = "user"):
    """Save the current session for a user, including last panel."""
    safe_name = safe_username_for_file(username)
    user_dir = os.path.join(SESSION_ROOT, safe_name)
    os.makedirs(user_dir, exist_ok=True)
    session_data = {
        "username": username,
        "role": role,
        "panel": panel,
        "last_login": datetime.utcnow().isoformat()
    }
    with open(os.path.join(user_dir, "session.json"), "w", encoding="utf-8") as f:
        json.dump(session_data, f, indent=4)
    print(f"[DEBUG] Session saved for {username} at {user_dir}")


def load_session(username: str) -> Optional[dict]:
    """Load session data for a given user."""
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_ROOT, safe_name, "session.json")
    if os.path.exists(session_file):
        with open(session_file, "r", encoding="utf-8") as f:
            return json.load(f)
    return None


def clear_session(username: str):
    """Remove only this user's session file."""
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_ROOT, safe_name, "session.json")
    if os.path.exists(session_file):
        os.remove(session_file)
        print(f"[DEBUG] Removed session file {session_file}")


def user_panel(page: ft.Page, username: Optional[str]):
    if not username:
        from login_window import login_view
        login_view(page)
        return

    # Save persistent session (with panel user)
    save_session(username, "USER", panel="user")

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
    notifications_popup = NotificationsWindow(page, username, approval_service)

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
        notifications_popup.hide()  # ADDED - Hide popup when changing views
        update_content()

    def show_files_view(): 
        nonlocal current_view
        current_view = "files"
        notifications_popup.hide()  # ADDED - Hide popup when changing views
        update_content()

    def show_approval_files_view(): 
        nonlocal current_view
        current_view = "approval_files"
        notifications_popup.hide()  # ADDED - Hide popup when changing views
        update_content()

    def show_notifications_view(): 
        nonlocal current_view
        current_view = "notifications"
        notifications_popup.hide()  # ADDED - Hide popup when changing views
        update_content()

    def show_browser_view(): 
        nonlocal current_view
        current_view = "browser"
        notifications_popup.hide()  # ADDED - Hide popup when changing views
        update_content()

    # ADDED - New function to show full-screen notifications popup
    def show_notifications_popup(e):
        """Show full-screen notifications popup"""
        notifications_popup.toggle()

    # ADDED - Callback for when notifications are updated
    def on_notifications_updated():
        """Update app bar when notifications change"""
        update_appbar()

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

    # ADDED - Set callback for notifications popup
    notifications_popup.set_close_callback(on_notifications_updated)

    def get_notification_status():
        try:
            unread_count = approval_service.get_unread_notification_count()
            if unread_count > 0:
                return f"({unread_count})", ft.Icons.NOTIFICATIONS_ACTIVE
            else:
                return "", ft.Icons.NOTIFICATIONS_NONE
        except:
            return "", ft.Icons.NOTIFICATIONS_NONE

    # ADDED - Separate function to update app bar
    def update_appbar():
        """Update only the app bar"""
        notification_badge, notification_icon = get_notification_status()
        
        page.appbar = ft.AppBar(
            title=ft.Text("", color=ft.Colors.WHITE),
            actions=[
                ft.Container(
                    content=ft.Stack([
                        ft.IconButton(
                            icon=notification_icon,
                            icon_color=ft.Colors.WHITE,
                            tooltip="Notifications",
                            on_click=show_notifications_popup  # CHANGED - Use popup instead of full page
                        ),
                        ft.Container(
                            content=ft.Text(
                                notification_badge,
                                size=10,
                                color=ft.Colors.WHITE,
                                weight=ft.FontWeight.BOLD
                            ),
                            bgcolor=ft.Colors.RED,
                            border_radius=8,
                            padding=ft.padding.symmetric(horizontal=4, vertical=2),
                            top=5,
                            right=5,
                            visible=bool(notification_badge)
                        )
                    ])
                ) if notification_badge else ft.IconButton(
                    icon=notification_icon,
                    icon_color=ft.Colors.WHITE,
                    tooltip="Notifications",
                    on_click=show_notifications_popup  # CHANGED - Use popup instead of full page
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
        page.update()

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