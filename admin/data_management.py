import flet as ft
from flet import FontWeight
from typing import Optional

def data_management(content: ft.Column, username: Optional[str]):
    # Clear existing controls
    content.controls.clear()

    content.controls.extend([
        ft.Text("Data Management", size=24, weight=FontWeight.BOLD),
        ft.Divider(),
        ft.Row([
            ft.ElevatedButton("Upload File", icon=ft.Icons.UPLOAD_FILE),
            ft.ElevatedButton("Create Folder", icon=ft.Icons.CREATE_NEW_FOLDER)
        ]),
        ft.Divider(),
        ft.Text("File browser content...")
    ])

    content.update()
