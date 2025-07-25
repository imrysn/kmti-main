import flet as ft
from flet import FontWeight, Icon
from typing import Optional

def activity_logs(page: ft.Page, username: Optional[str]):
    def load_logs():
        with open("data/logs/activity.log", "r") as f:
            return f.readlines()[-100:]  # Get last 100 lines
    
    logs = load_logs()
    log_view = ft.Column(scroll=ft.ScrollMode.AUTO, expand=True)
    
    for log in reversed(logs):  # Show newest first
        log_view.controls.append(ft.Text(log.strip()))
    
    page.add(
        ft.Column([
            ft.Text("Activity Logs", size=24, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.Row([
                ft.TextField(label="Filter logs...", expand=True),
                ft.ElevatedButton("Export Logs")
            ]),
            ft.Divider(),
            log_view
        ], expand=True)
    )