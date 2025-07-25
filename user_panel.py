import flet as ft
import os
from utils.file_manager import save_file
from utils.logger import log_action
from flet import FontWeight, ScrollMode, CrossAxisAlignment
from typing import Optional

def user_panel(page: ft.Page, username: Optional[str]):
    user_folder = f"data/uploads/{username}"
    os.makedirs(user_folder, exist_ok=True)

    def logout(e):
        page.clean()
        from login_window import login_view
        login_view(page)

    def upload_file(e: ft.FilePickerResultEvent):
        if e.files:
            for f in e.files:
                save_file(f, user_folder)
                log_action(username, f"Uploaded file: {f.name}")
        refresh_files()

    def refresh_files():
        file_list.controls.clear()
        if os.path.exists(user_folder):
            for fname in os.listdir(user_folder):
                file_list.controls.append(ft.Text(fname))
        page.update()

    file_picker = ft.FilePicker(on_result=upload_file)
    file_list = ft.Column()

    page.overlay.append(file_picker)
    page.appbar = ft.AppBar(title=ft.Text("User Dashboard"), actions=[ft.TextButton("Logout", on_click=logout)])

    page.add(
        ft.Column([
            ft.Text(f"Welcome, {username}!", size=20, weight=FontWeight.BOLD),
            ft.ElevatedButton("Upload File", on_click=lambda _: file_picker.pick_files(allow_multiple=True)),
            ft.Text("Your Files:", size=16, weight=FontWeight.BOLD),
            file_list,
        ], scroll=ScrollMode.AUTO, expand=True)
    )
    refresh_files()
