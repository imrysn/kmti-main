import flet as ft
import json
from utils.logger import log_action
from utils.session_logger import log_logout
from flet import FontWeight, ScrollMode, CrossAxisAlignment, MainAxisAlignment, Colors
from typing import Optional
from admin.navbar import create_navbar
from admin.data_management import data_management
from admin.activity_logs import activity_logs
from admin.system_settings import system_settings
from admin.user_management import user_management


def admin_panel(page: ft.Page, username: Optional[str], initial_tab: int = 0):
    # macOS-inspired colors
    BACKGROUND = ft.Colors.GREY_100
    PANEL_COLOR = "#FFFFFF"
    PANEL_RADIUS = 14

    # Page properties
    page.title = "KMTI Data Management Admin"
    page.vertical_alignment = MainAxisAlignment.START
    page.horizontal_alignment = CrossAxisAlignment.START
    page.bgcolor = BACKGROUND

    # Logout
    def logout(e):
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

    content = ft.Column(scroll=ScrollMode.AUTO, expand=True, spacing=20)
    users = load_users()
    logs = load_logs()

    def get_user_status(data):
        return data.get('status', 'Unknown')

    # Card helper for macOS style
    def card(title_icon, title, value, icon_color=Colors.BLACK):
        return ft.Container(
            content=ft.Column(
                [
                    ft.Icon(title_icon, size=40, color=icon_color),
                    ft.Text(title, size=16, color="#333333"),
                    ft.Text(value, size=26, weight=FontWeight.BOLD, color="#000000"),
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=8,
            ),
            padding=20,
            bgcolor=PANEL_COLOR,
            border_radius=PANEL_RADIUS,
            shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            width=220,
            height=160,
        )

    def show_dashboard():
        content.controls.clear()

        total_users = len(users)
        active_users = sum(1 for u in users.values() if get_user_status(u) == 'Active')

        content.controls.extend([
            ft.Row([
                card(ft.Icons.PEOPLE, "Total Users", str(total_users)),
                card(ft.Icons.PERSON, "Active Users", str(active_users), icon_color=Colors.GREEN),
                card(ft.Icons.HISTORY, "Recent Activities", str(len(logs)), icon_color=Colors.BLUE),
            ], spacing=20),

            ft.Text("Recent Users", size=22, weight=FontWeight.BOLD, color="#111111"),
            ft.Container(
                content=ft.DataTable(
                    heading_row_color="#FAFAFA",
                    columns=[
                        ft.DataColumn(ft.Text("Name", weight=FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Email", weight=FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Status", weight=FontWeight.BOLD)),
                        ft.DataColumn(ft.Text("Actions", weight=FontWeight.BOLD))
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
                                ], spacing=8))
                            ]
                        ) for email, data in list(users.items())[:5]
                    ],
                ),
                bgcolor=PANEL_COLOR,
                border_radius=PANEL_RADIUS,
                padding=20,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            ),

            ft.Text("Recent Activities", size=22, weight=FontWeight.BOLD, color="#111111"),
            ft.Container(
                content=ft.ListView(
                    [ft.Text(line.strip(), color="#333333") for line in reversed(logs[-10:])],
                    height=200,
                    spacing=5
                ),
                bgcolor=PANEL_COLOR,
                border_radius=PANEL_RADIUS,
                padding=20,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            ),
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

    # Top navbar
    top_nav = create_navbar(username, navigate_to_section, lambda: logout(None))

    # Layout
    page.controls.clear()
    page.add(
        ft.Column(
            [
                top_nav,
                ft.Container(
                    content=content,
                    expand=True,
                    padding=20,
                )
            ],
            spacing=10,
            expand=True,
        )
    )

    # Initial tab
    navigate_to_section(initial_tab)

    log_action(username, "Login")
