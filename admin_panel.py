import flet as ft
import json
from utils.logger import log_action
from utils.session_logger import log_logout  # FIXED IMPORT
from flet import FontWeight, ScrollMode, CrossAxisAlignment, MainAxisAlignment, Colors
from typing import Optional
from admin.navbar import create_navbar
from admin.data_management import data_management
from admin.activity_logs import activity_logs
from admin.system_settings import system_settings
from admin.user_management import user_management


def admin_panel(page: ft.Page, username: Optional[str], initial_tab: int = 0):
    # Page properties
    page.title = "KMTI Data Management Admin"
    page.vertical_alignment = MainAxisAlignment.START
    page.horizontal_alignment = CrossAxisAlignment.START
    page.bgcolor = "#f5f5f5"

    # Logout function
    def logout(e):
        # Log logout with runtime calculation
        log_logout(username, "admin")
        log_action(username, "Logged out")
        page.clean()
        from login_window import login_view
        login_view(page)

    # Load users and logs
    def load_users():
        try:
            with open("data/users.json", "r") as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def load_logs():
        try:
            with open("data/logs/activity.log", "r") as f:
                return f.readlines()[-100:]
        except FileNotFoundError:
            return ["No activity logs found"]

    content = ft.Column(scroll=ScrollMode.AUTO, expand=True)
    users = load_users()
    logs = load_logs()

    def get_user_status(data):
        return data.get('status', 'Unknown')

    def show_dashboard():
        content.controls.clear()

        total_users = len(users)
        active_users = sum(1 for u in users.values() if get_user_status(u) == 'Active')

        content.controls.extend([
            ft.Row([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PEOPLE, size=40),
                        ft.Text("Total Users", size=16),
                        ft.Text(str(total_users), size=24, weight=FontWeight.BOLD)
                    ], horizontal_alignment=CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=Colors.WHITE,
                    border_radius=10,
                    width=200,
                    height=150
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.PERSON, size=40),
                        ft.Text("Active Users", size=16),
                        ft.Text(str(active_users), size=24, weight=FontWeight.BOLD)
                    ], horizontal_alignment=CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=Colors.WHITE,
                    border_radius=10,
                    width=200,
                    height=150
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.HISTORY, size=40),
                        ft.Text("Recent Activities", size=16),
                        ft.Text(str(len(logs)), size=24, weight=FontWeight.BOLD)
                    ], horizontal_alignment=CrossAxisAlignment.CENTER),
                    padding=20,
                    bgcolor=Colors.WHITE,
                    border_radius=10,
                    width=200,
                    height=150
                )
            ], spacing=20),

            ft.Divider(height=40),

            ft.Text("Recent Users", size=20, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("Name")),
                    ft.DataColumn(ft.Text("Email")),
                    ft.DataColumn(ft.Text("Status")),
                    ft.DataColumn(ft.Text("Actions"))
                ],
                rows=[
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(data.get('fullname', 'Unknown'))),
                            ft.DataCell(ft.Text(email)),
                            ft.DataCell(ft.Text(
                                get_user_status(data),
                                color={
                                    "Active": Colors.GREEN,
                                    "Inactive": Colors.ORANGE,
                                    "Banned": Colors.RED
                                }.get(get_user_status(data), Colors.GREY)
                            )),
                            ft.DataCell(ft.Row([
                                ft.IconButton(ft.Icons.EDIT, tooltip="Edit"),
                                ft.IconButton(ft.Icons.LOCK_RESET, tooltip="Reset Password"),
                                ft.IconButton(ft.Icons.DELETE, tooltip="Delete", icon_color=Colors.RED)
                            ]))
                        ]
                    ) for email, data in list(users.items())[:5]
                ],
            ),

            ft.Divider(height=40),

            ft.Text("Recent Activities", size=20, weight=FontWeight.BOLD),
            ft.Divider(),
            ft.ListView(
                [ft.Text(line.strip()) for line in reversed(logs[-10:])],
                height=200,
                spacing=5
            )
        ])
        content.update()

    # Navigation handler
    def navigate_to_section(index: int):
        content.controls.clear()
        if index == 0:
            show_dashboard()
        elif index == 1:
            data_management(content, username)
        elif index == 2:
            user_management(content, username)
        elif index == 3:
            activity_logs(content, username)
        elif index == 4:
            system_settings(content, username)

    # Create top navbar
    top_nav = create_navbar(username, navigate_to_section, lambda: logout(None))

    # Layout
    page.controls.clear()
    page.add(
        ft.Column(
            [
                top_nav,
                content
            ],
            spacing=10,
            expand=True,
        )
    )

    # Show initial tab
    navigate_to_section(initial_tab)

    log_action(username, "Logged into admin panel")
