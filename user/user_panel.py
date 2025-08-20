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
from admin.components.role_colors import create_role_badge, get_role_color
from utils.path_config import DATA_PATHS

# Use consistent session management with login_window.py
SESSION_ROOT = DATA_PATHS.local_sessions_dir

def safe_username_for_file(username: str) -> str:
    """Return a filename-safe username."""
    return "".join(c for c in (username or "") if c.isalnum() or c in ("-", "_")).strip() or "user"

def save_session(username: str, role: str = "user", panel: str = "user"):
    """Save session per user including which panel was opened and login_time."""
    print(f"[DEBUG] Saving session for {username} with role {role}, panel={panel}")
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_ROOT, f"{safe_name}.json")
    os.makedirs(SESSION_ROOT, exist_ok=True)
    
    session_payload = {
        "username": username,
        "role": role,
        "panel": panel,
        "login_time": datetime.utcnow().isoformat()
    }
    
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_payload, f, indent=4)
        print(f"[DEBUG] Saved session for {username} -> {session_file}")
    except Exception as ex:
        print(f"[DEBUG] save_session error: {ex}")

def clear_session(username: str):
    """Clear session per user (on explicit logout)."""
    print(f"[DEBUG] Clearing session for {username}")
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_ROOT, f"{safe_name}.json")
    
    try:
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"[DEBUG] Cleared session for {username}")
    except Exception as ex:
        print(f"[DEBUG] clear_session error: {ex}")

def user_panel(page: ft.Page, username: Optional[str]):
    """User panel - accessible only by USER role users."""
    # Verify user has user role
    from utils.auth import load_users
    users = load_users()
    user_role = None
    for email, data in users.items():
        if data.get("username") == username:
            user_role = data.get("role", "").upper()
            # Normalize role string
            if user_role == "TEAM LEADER":
                user_role = "TEAM_LEADER"
            break
    
    print(f"[DEBUG] User panel access check: username={username}, role={user_role}")
    
    if user_role != "USER":
        print(f"[WARNING] Non-user role {user_role} attempted to access user panel")
        page.clean()
        from login_window import login_view
        login_view(page)
        return
    
    # Clear any existing page state first
    page.controls.clear()
    page.appbar = None
    page.overlay.clear()
    
    # Set page properties for user panel
    page.title = "KMTI Data Management Users"
    page.bgcolor = ft.Colors.GREY_200
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.padding = 0
    page.margin = 0
    
    # Force page update to clear login screen
    page.update()
    
    save_session(username, "USER", "user")

    # Use network path for user folder
    user_folder = DATA_PATHS.get_user_upload_dir(username)
    DATA_PATHS.ensure_user_dirs(username)
    
    # Initialize services with network paths
    profile_service = ProfileService(user_folder, username)
    file_service = FileService(user_folder, username)
    approval_service = ApprovalFileService(user_folder, username)
    
    # Initialize views
    browser_view = BrowserView(page, username)
    profile_view = ProfileView(page, username, profile_service)
    files_view = FilesView(page, username, file_service)
    approval_files_view = ApprovalFilesView(page, username, approval_service)
    notifications_view = NotificationsView(page, username, approval_service)
    notifications_popup = NotificationsWindow(page, username, approval_service)

    current_view = "browser"
    # ADD: Track highlighted file for navigation from notifications
    highlighted_file = None

    log_action(username, "Login")
    log_activity(username, "Login")

    def logout(e):
        log_action(username, "Logout")
        log_activity(username, "Logout")
        clear_session(username)  # Pass username parameter
        page.controls.clear()
        page.appbar = None
        page.overlay.clear()
        page.title = "Login"
        page.bgcolor = None
        page.update()
        from login_window import login_view
        login_view(page)
    
    def show_profile_view():
        nonlocal current_view, highlighted_file
        print("[DEBUG] Switching to Profile view")
        current_view = "profile"
        highlighted_file = None  # Clear highlight when switching views
        notifications_popup.hide()
        update_content()
    
    def show_files_view():
        nonlocal current_view, highlighted_file
        print("[DEBUG] Switching to Files view")
        current_view = "files"
        highlighted_file = None  # Clear highlight when switching views
        notifications_popup.hide()
        update_content()
    
    # MODIFIED: Support highlighting specific files
    def show_approval_files_view(highlight_filename=None):
        nonlocal current_view, highlighted_file
        print(f"[DEBUG] Switching to Approval Files view, highlighting: {highlight_filename}")
        current_view = "approval_files"
        highlighted_file = highlight_filename  # Set the file to highlight
        notifications_popup.hide()
        update_content()
    
    def show_notifications_view():
        nonlocal current_view, highlighted_file
        print("[DEBUG] Switching to Notifications view")
        current_view = "notifications"
        highlighted_file = None  # Clear highlight when switching views
        notifications_popup.hide()
        update_content()
    
    def show_browser_view():
        nonlocal current_view, highlighted_file
        print("[DEBUG] Switching to Browser view")
        current_view = "browser"
        highlighted_file = None  # Clear highlight when switching views
        notifications_popup.hide()
        update_content()

    def show_notifications_popup(e):
        """Show full-screen notifications popup"""
        print("[DEBUG] Showing notifications popup")
        notifications_popup.toggle()

    def on_notifications_updated():
        """Update app bar when notifications change"""
        update_appbar()

    # ADD: Handler for file clicks from notifications
    def on_notification_file_click(filename: str):
        """Handle file click from notifications - navigate to file approvals with highlight"""
        print(f"[DEBUG] File clicked from notification: {filename}")
        show_approval_files_view(highlight_filename=filename)

    navigation = {
        'show_profile': show_profile_view,
        'show_files': show_files_view,
        'show_approval_files': show_approval_files_view,
        'show_notifications': show_notifications_view,
        'show_browser': show_browser_view,
        'on_notification_file_click': on_notification_file_click  # ADD: File click handler
    }
    
    # Set navigation for all views
    browser_view.set_navigation(navigation)
    profile_view.set_navigation(navigation)
    files_view.set_navigation(navigation)
    approval_files_view.set_navigation(navigation)
    notifications_view.set_navigation(navigation)

    # Set callback for notifications popup
    notifications_popup.set_close_callback(on_notifications_updated)
    # ADD: Set navigation for notifications popup
    notifications_popup.set_navigation(navigation)

    def get_notification_status():
        """Get notification count and text for app bar"""
        try:
            unread_count = approval_service.get_unread_notification_count()
            if unread_count > 0:
                return f"({unread_count})", ft.Icons.NOTIFICATIONS_ACTIVE
            else:
                return "", ft.Icons.NOTIFICATIONS_NONE
        except:
            return "", ft.Icons.NOTIFICATIONS_NONE

    def update_appbar():
        """Update app bar - REMOVED 'User Dashboard' title and adjusted text sizes"""
        notification_badge, notification_icon = get_notification_status()
        
        page.appbar = ft.AppBar(
            title=ft.Text(""),  # REMOVED "User Dashboard" - now empty
            actions=[
                ft.Container(
                    content=ft.Stack([
                        ft.IconButton(
                            icon=notification_icon,
                            icon_color=ft.Colors.WHITE,
                            tooltip="Notifications",
                            on_click=show_notifications_popup
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
                    on_click=show_notifications_popup
                ),
                ft.TextButton(
                    f"Hi, {username}" if username else "Hi, User",
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        text_style=ft.TextStyle(size=16)  # INCREASED text size from default to 16
                    ),
                    on_click=lambda e: show_profile_view()
                ),
                ft.TextButton(
                    "Logout", 
                    style=ft.ButtonStyle(
                        color=ft.Colors.WHITE,
                        text_style=ft.TextStyle(size=16)  # INCREASED text size from default to 16
                    ),
                    on_click=logout
                )
            ],
            bgcolor=ft.Colors.GREY_800
        )
        page.update()

    def update_content():
        """Update content with robust error handling and forced UI refresh"""
        print(f"[DEBUG] Updating content to: {current_view}, highlighted_file: {highlighted_file}")
        try:
            # Clear current content completely
            page.controls.clear()
            page.appbar = None
            
            # Force page update to clear any existing content
            page.update()
            
            # Get the appropriate content based on current view
            if current_view == "profile":
                content = profile_view.create_content()
                print("[DEBUG] Created profile content")
            elif current_view == "files":
                content = files_view.create_content()
                print("[DEBUG] Created files content")
            elif current_view == "approval_files":
                # MODIFIED: Pass highlighted file to approval files view
                content = approval_files_view.create_content(highlighted_filename=highlighted_file)
                print(f"[DEBUG] Created approval files content with highlighted file: {highlighted_file}")
            elif current_view == "notifications":
                content = notifications_view.create_content()
                print("[DEBUG] Created notifications content")
            else:
                content = browser_view.create_content()
                print("[DEBUG] Created browser content")

            # Update app bar first
            update_appbar()
            
            # Add new content
            if content:
                page.add(content)
            else:
                print("[ERROR] Content is None - creating fallback")
                page.add(ft.Text("Loading...", size=20))
            
            # Force final page update
            page.update()
            
            print(f"[DEBUG] Successfully updated to {current_view}")
            
        except Exception as e:
            print(f"[ERROR] Failed to update content: {e}")
            import traceback
            traceback.print_exc()
            
            # Show error message with retry option
            page.controls.clear()
            page.add(ft.Column([
                ft.Text(f"UI Error: {e}", color=ft.Colors.RED, size=16),
                ft.Text("Trying to recover...", color=ft.Colors.ORANGE),
                ft.ElevatedButton(
                    "Retry",
                    on_click=lambda e: update_content(),
                    bgcolor=ft.Colors.BLUE,
                    color=ft.Colors.WHITE
                )
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER))
            page.update()

    # Initialize page
    page.title = "KMTI Data Management Users"
    page.bgcolor = ft.Colors.GREY_200
    update_content()
