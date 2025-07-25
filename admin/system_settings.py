import flet as ft
from flet import FontWeight
from typing import Optional

def system_settings(page: ft.Page, username: Optional[str]):
    page.add(
        ft.Column([
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
        ], expand=True)
    )