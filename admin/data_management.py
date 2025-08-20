# data_management.py - Using BrowserView directly

import flet as ft
from typing import Optional
from pathlib import Path
import shutil
from utils.dialog import show_input_dialog
from user.components.browser_view import BrowserView

def data_management(content: ft.Column, username: Optional[str]):
    """Admin Data Management using BrowserView with admin-specific enhancements"""
    print("[DEBUG] Initializing admin data management UI using BrowserView")
    content.controls.clear()

    page = content.page

    # Create BrowserView instance
    browser = BrowserView(page, username or "admin")
    
    # Get the main layout from browser_view
    main_layout = browser.create_content()
    
    # Add admin-specific functionality
    def upload_files():
        """Admin file upload functionality"""
        def handle_files(e: ft.FilePickerResultEvent):
            if e.files:
                for f in e.files:
                    dst = browser.current_path[0] / Path(f.name).name
                    shutil.copy(f.path, dst)
                browser.refresh()

        existing = next((c for c in page.overlay if isinstance(c, ft.FilePicker)), None)
        if existing:
            existing.on_result = handle_files
            existing.pick_files(allow_multiple=True)
        else:
            file_picker = ft.FilePicker(on_result=handle_files)
            page.overlay.append(file_picker)
            page.update()
            file_picker.pick_files(allow_multiple=True)

    def create_new_folder():
        """Admin folder creation functionality"""
        def on_submit(name):
            if not name:
                return
            new = browser.current_path[0] / name
            try:
                new.mkdir(exist_ok=False)
                browser.refresh()
            except FileExistsError:
                page.snack_bar = ft.SnackBar(ft.Text("Folder already exists"), open=True)
                page.update()
            except PermissionError:
                page.snack_bar = ft.SnackBar(ft.Text("Permission denied: cannot create folder here"), open=True)
                page.update()

        show_input_dialog(page, "Create New Folder", "Folder name", on_submit)

    # Add admin buttons to the toolbar
    # Find the toolbar row and add admin-specific buttons
    try:
        toolbar_row = main_layout.controls[0].content.controls[0].controls[0]  # Navigate to toolbar row
        
        # Add spacer
        toolbar_row.controls.insert(1, ft.Container(width=10))
        
        # Add Upload button
        toolbar_row.controls.insert(2,
            ft.ElevatedButton(
                icon=ft.Icons.UPLOAD,
                text="Upload",
                on_click=lambda e: upload_files(),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                             ft.ControlState.HOVERED: ft.Colors.GREEN},
                    color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                    side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN)},
                    shape=ft.RoundedRectangleBorder(radius=5))
            )
        )
        
        # Add New Folder button
        toolbar_row.controls.insert(3,
            ft.ElevatedButton(
                icon=ft.Icons.CREATE_NEW_FOLDER,
                text="New Folder",
                on_click=lambda e: create_new_folder(),
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                             ft.ControlState.HOVERED: ft.Colors.BLUE},
                    color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                    side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE)},
                    shape=ft.RoundedRectangleBorder(radius=5))
            )
        )
    except Exception as ex:
        print(f"[WARNING] Could not add admin buttons to toolbar: {ex}")

    # Add the browser layout to content
    content.controls.append(main_layout)
    content.update()
    
    # Initialize the browser view
    browser.initialize_view()
    
    print("[DEBUG] Admin data management initialized successfully using BrowserView")