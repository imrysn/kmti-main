import flet as ft
import os
import json
from typing import Optional

from .components.browser_view import BrowserView
from .components.profile_view import ProfileView
from .components.files_view import FilesView
from .services.profile_service import ProfileService
from .services.file_service import FileService
from utils.logger import log_action  
from utils.session_logger import log_activity

SESSION_FILE = "data/session.json"

def save_session(username: str, role: str = "user"):
    print(f"[DEBUG] Saving session for {username} with role {role}")
    os.makedirs("data", exist_ok=True)
    with open(SESSION_FILE, "w") as f:
        json.dump({"username": username, "role": role}, f)

def clear_session():
    print("[DEBUG] Clearing session")
    if os.path.exists(SESSION_FILE):
        os.remove(SESSION_FILE)

def user_panel(page: ft.Page, username: Optional[str]):
    save_session(username, "user")

    user_folder = f"data/uploads/{username}"
    os.makedirs(user_folder, exist_ok=True)
    
    profile_service = ProfileService(user_folder, username)
    file_service = FileService(user_folder, username)
    
    browser_view = BrowserView(page, username)
    profile_view = ProfileView(page, username, profile_service)
    files_view = FilesView(page, username, file_service)

    current_view = "browser"

    log_action(username, "Login")
    log_activity(username, "Login")

    def logout(e):
        log_action(username, "Logout")
        log_activity(username, "Logout")
        clear_session()
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
    
    def show_browser_view():
        nonlocal current_view
        current_view = "browser"
        update_content()

    navigation = {
        'show_profile': show_profile_view,
        'show_files': show_files_view,
        'show_browser': show_browser_view
    }
    
    browser_view.set_navigation(navigation)
    profile_view.set_navigation(navigation)
    files_view.set_navigation(navigation)

    def update_content():
        print(f"[DEBUG] Updating content: {current_view}")
        try:
            if current_view == "profile":
                content = profile_view.create_content()
            elif current_view == "files":
                content = files_view.create_content()
            else:
                content = browser_view.create_content()

            page.controls.clear()
            page.appbar = ft.AppBar(
                title=ft.Text("User Dashboard", color=ft.Colors.WHITE),
                actions=[
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

    # Initialize page
    page.title = "KMTI Data Management Users"
    page.bgcolor = ft.Colors.GREY_200
    update_content()