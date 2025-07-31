import flet as ft
import json
import os
from datetime import datetime
from utils.logger import log_action
from utils.session_logger import log_logout
from flet import FontWeight, ScrollMode, CrossAxisAlignment, MainAxisAlignment, Colors
from typing import Optional
from admin.navbar import create_navbar
from admin.data_management import data_management
from admin.activity_logs import activity_logs
from admin.system_settings import system_settings
from admin.user_management import user_management

USERS_FILE = "data/users.json"
ACTIVITY_LOGS_FILE = "data/logs/activity_logs.json"
ACTIVITY_METADATA_FILE = "data/logs/activity_metadata.json"


def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default


def admin_panel(page: ft.Page, username: Optional[str], initial_tab: int = 0):
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

    # Data loaders
    def load_users():
        return load_json(USERS_FILE, {})

    def load_logs():
        return load_json(ACTIVITY_LOGS_FILE, [])

    def load_metadata():
        return load_json(ACTIVITY_METADATA_FILE, {})

    content = ft.Column(
        scroll=ScrollMode.AUTO,
        expand=True,
        spacing=20,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )
    users = load_users()
    logs = load_logs()
    metadata = load_metadata()

    # Filter logs for today's date
    today = datetime.now().strftime("%Y-%m-%d")
    today_logs = [log for log in logs if log.get("date", "").startswith(today)]

    # Card helper
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
            shadow=ft.BoxShadow(
                blur_radius=8,
                spread_radius=1,
                color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            ),
            width=220,
            height=160,
        )

        # Get login status of a user
    def get_login_status(user_email, user_data):
        uname = user_data.get("username")
        is_online = False

        # If metadata is a list
        if isinstance(metadata, list):
            for entry in metadata:
                if entry.get("username") == uname:
                    if entry.get("login_time") and entry.get("logout_time") is None:
                        is_online = True
                    break
        # If metadata is a dict (legacy)
        elif isinstance(metadata, dict):
            entry = metadata.get(uname, {})
            if entry.get("login_time") and entry.get("logout_time") is None:
                is_online = True

        # Return colored text
        return ft.Text(
            "Online" if is_online else "Offline",
            color=Colors.GREEN if is_online else Colors.RED,
            weight=FontWeight.BOLD
        )

    def show_dashboard():
        content.controls.clear()

        total_users = len(users)

        # Count active users
        active_users = 0
        if isinstance(metadata, list):
            active_users = sum(
                1
                for entry in metadata
                if isinstance(entry, dict)
                and entry.get("login_time")
                and entry.get("logout_time") is None
            )
        elif isinstance(metadata, dict):
            active_users = sum(
                1
                for u in metadata.values()
                if isinstance(u, dict)
                and u.get("login_time")
                and u.get("logout_time") is None
            )

        recent_activity_count = len(today_logs)

        # Dashboard cards
        content.controls.append(
            ft.Row(
                [
                    card(ft.Icons.PEOPLE, "Total Users", str(total_users)),
                    card(
                        ft.Icons.PERSON,
                        "Active Users",
                        str(active_users),
                        icon_color=Colors.GREEN,
                    ),
                    card(
                        ft.Icons.HISTORY,
                        "Recent Activities",
                        str(recent_activity_count),
                        icon_color=Colors.BLUE,
                    ),
                ],
                spacing=20,
                alignment=MainAxisAlignment.CENTER,
            )
        )

        # Recent Users Table
        content.controls.append(
            ft.Text("Recent Users", size=22, weight=FontWeight.BOLD, color="#111111")
        )

        users_table = ft.DataTable(
            heading_row_color="#FAFAFA",
            columns=[
                ft.DataColumn(ft.Text("Name", weight=FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Email", weight=FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=FontWeight.BOLD)),
            ],
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(data.get("fullname", "Unknown"))),
                        ft.DataCell(ft.Text(email)),
                        ft.DataCell(get_login_status(email, data)),

                    ]
                )
                for email, data in list(users.items())[:5]
            ],
        )

        content.controls.append(
            ft.Container(
                content=ft.Row([users_table], alignment=MainAxisAlignment.CENTER),
                bgcolor=PANEL_COLOR,
                border_radius=PANEL_RADIUS,
                padding=20,
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                ),
            )
        )

        # Recent Activities Table
        content.controls.append(
            ft.Text("Recent Activities", size=22, weight=FontWeight.BOLD, color="#111111")
        )

        # Build user info lookup
        user_info = {}
        for email, data in users.items():
            uname = data.get("username")
            if uname:
                team = data.get("team_tags", [])
                team_str = (
                    ", ".join(team)
                    if isinstance(team, list)
                    else (str(team) if team else "")
                )
                user_info[uname] = {
                    "fullname": data.get("fullname", uname),
                    "email": email,
                    "role": data.get("role", ""),
                    "team": team_str,
                }

        rows = []
        for log in reversed(today_logs[-10:]):
            uname = log.get("username", "")
            info = user_info.get(
                uname,
                {"fullname": uname, "email": "", "role": "", "team": ""},
            )
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(info["fullname"])),
                        ft.DataCell(ft.Text(info["email"])),
                        ft.DataCell(ft.Text(uname)),
                        ft.DataCell(ft.Text(info["role"])),
                        ft.DataCell(ft.Text(info["team"])),
                        ft.DataCell(ft.Text(log.get("date", "-"))),
                        ft.DataCell(ft.Text(log.get("activity", ""))),
                    ]
                )
            )

        activities_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Full Name")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Team")),
                ft.DataColumn(ft.Text("Date & Time")),
                ft.DataColumn(ft.Text("Activity")),
            ],
            rows=rows,
        )

        content.controls.append(
            ft.Container(
                content=ft.Row([activities_table], alignment=MainAxisAlignment.CENTER),
                bgcolor=PANEL_COLOR,
                border_radius=PANEL_RADIUS,
                padding=20,
                shadow=ft.BoxShadow(
                    blur_radius=8,
                    spread_radius=1,
                    color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
                ),
            )
        )

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
                ),
            ],
            spacing=10,
            expand=True,
        )
    )

    # Initial tab
    navigate_to_section(initial_tab)

    log_action(username, "Login")
