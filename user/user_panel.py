import flet as ft
import os
from typing import Optional

from .components.browser_view import BrowserView
from .components.profile_view import ProfileView
from .components.files_view import FilesView
from .services.profile_service import ProfileService
from .services.file_service import FileService
from utils.logger import log_action  
from utils.session_logger import log_activity


def user_panel(page: ft.Page, username: Optional[str]):
    """Main user panel function - orchestrates the different views and services"""
    
    # Initialize services
    user_folder = f"data/uploads/{username}"
    os.makedirs(user_folder, exist_ok=True)
    
    profile_service = ProfileService(user_folder, username)
    file_service = FileService(user_folder, username)
    
    # Initialize views
    browser_view = BrowserView(page, username)
    profile_view = ProfileView(page, username, profile_service)
    files_view = FilesView(page, username, file_service)
    
    # Current view state
    current_view = "browser"

    # Log that user entered the panel
    log_action(username, "Login")
    log_activity(username, "Login")

    def logout(e):
        # Log logout event
        log_action(username, "Logged")
        log_activity(username, "Logout")

        # Clear all page elements completely
        page.controls.clear()
        page.appbar = None  # Remove the app bar
        page.overlay.clear()  # Clear overlays (file picker, etc.)
        
        # Reset page properties
        page.title = "Login"
        page.bgcolor = None
        
        # Update the page to reflect changes
        page.update()
        
        # Import and call login view
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
    
    # Pass navigation functions to views
    navigation = {
        'show_profile': show_profile_view,
        'show_files': show_files_view,
        'show_browser': show_browser_view
    }
    
    browser_view.set_navigation(navigation)
    profile_view.set_navigation(navigation)
    files_view.set_navigation(navigation)
    
    def update_content():
        """Update the main content based on current view"""
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
            bgcolor=ft.Colors.GREY_700
        )
        page.add(content)
        page.update()
    
    # Initialize page
    page.title = "KMTI Data Management Users"
    page.bgcolor = ft.Colors.GREY_200
    update_content()
