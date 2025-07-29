import flet as ft
from flet import FontWeight
from typing import Optional

def system_settings(content: ft.Column, username: Optional[str]):
    # Clear previous content
    content.controls.clear()

    content.controls.extend([
        ft.Text("System Settings", size=24, weight=FontWeight.BOLD),
        ft.Divider(),
        ft.Text("Application Settings"),
        ft.Switch(label="Maintenance Mode"),
        ft.TextField(label="System Name", value="KMTI System"),
        ft.Divider(),
        ft.Text("Email Settings"),
        ft.TextField(label="SMTP Server"),
        ft.TextField(label="Admin Email"),
        ft.ElevatedButton("Save Settings")
    ])

    content.update()
