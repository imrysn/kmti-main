import flet as ft
import json
from utils.logger import log_action
from flet import FontWeight, ScrollMode, CrossAxisAlignment
from typing import Optional

def admin_panel(page: ft.Page, username: Optional[str]):
    def logout(e):
        page.clean()
        from login_window import login_view
        login_view(page)

    def load_users():
        with open("data/users.json", "r") as f:
            return json.load(f)

    users = load_users()
    user_cards = []
    for email, data in users.items():
        user_cards.append(ft.Text(f"{data['fullname']} - {email} - {data['role']}"))

    with open("data/logs/activity.log", "r") as f:
        logs = f.readlines()

    page.appbar = ft.AppBar(title=ft.Text("Admin Dashboard"), actions=[ft.TextButton("Logout", on_click=logout)])
    page.add(
        ft.Column([
            ft.Text("Users", size=20, weight=FontWeight.BOLD),
            ft.Column(user_cards),
            ft.Divider(),
            ft.Text("Activity Logs", size=20, weight=FontWeight.BOLD),
            ft.Column([ft.Text(line.strip()) for line in logs[-10:]]),
        ], scroll=ScrollMode.AUTO, expand=True, spacing=15)
    )

    log_action(username, "Logged into admin panel")
