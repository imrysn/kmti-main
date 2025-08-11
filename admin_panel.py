import flet as ft
import json
import os
from datetime import datetime
from typing import Optional

from utils.session_logger import log_logout, log_activity
from admin.navbar import create_navbar
from admin.data_management import data_management
from admin.activity_logs import activity_logs
from admin.system_settings import system_settings
from admin.user_management import user_management
from user.user_panel import save_session, clear_session
from admin.components.file_approval_panel import FileApprovalPanel

USERS_FILE = "data/users.json"
ACTIVITY_LOGS_FILE = "data/logs/activity_logs.json"
ACTIVITY_METADATA_FILE = "data/logs/activity_metadata.json"
SESSION_BASE_DIR = "sessions"

def load_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, "r") as f:
            return json.load(f)
    except json.JSONDecodeError:
        return default

def load_users():
    return load_json(USERS_FILE, {})

def load_logs():
    return load_json(ACTIVITY_LOGS_FILE, [])

def load_metadata():
    return load_json(ACTIVITY_METADATA_FILE, {})

def get_session_path(username: str):
    """Get the per-user session file path."""
    user_dir = os.path.join(SESSION_BASE_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    return os.path.join(user_dir, "session.json")

def session_exists(username: str) -> bool:
    """Check if a saved session exists for the given user."""
    return os.path.exists(get_session_path(username))

def admin_panel(page: ft.Page, username: Optional[str], initial_tab: int = 0):
    BACKGROUND = ft.Colors.GREY_100
    PANEL_COLOR = "#FFFFFF"
    PANEL_RADIUS = 14

    page.title = "KMTI Data Management Admin"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.margin = 0

    def logout(e):
        print(f"[DEBUG] logout() called by username={username}")
        log_logout(username, "admin")
        log_activity(username, "Logout")
        clear_session(username)  # deletes sessions/<username>/session.json
        page.clean()
        from login_window import login_view
        login_view(page)

    content = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=20,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def get_last_activity_entry(username_lookup: str):
        fresh_logs = load_logs()
        for entry in reversed(fresh_logs):
            if entry.get("username") == username_lookup:
                return entry
        return None

    def is_user_online(user_data) -> bool:
        uname = user_data.get("username")
        if not uname:
            return False
        last_entry = get_last_activity_entry(uname)
        return last_entry and last_entry.get("activity") == "Login"

    def get_login_status(user_email, user_data):
        online = is_user_online(user_data)
        return ft.Text(
            "Online" if online else "Offline",
            color=ft.Colors.GREEN if online else ft.Colors.RED,
            weight=ft.FontWeight.BOLD
        )

    def show_dashboard():
        content.controls.clear()
        users = load_users()
        fresh_logs = load_logs()

        def parse_datetime(log):
            try:
                return datetime.strptime(log.get("date", ""), "%Y-%m-%d %H:%M:%S")
            except Exception:
                return datetime.min

        fresh_logs.sort(key=parse_datetime)

        total_users = len(users)
        active_users = sum(1 for u in users.values() if is_user_online(u))
        recent_activity_count = len(fresh_logs)

        refresh_button = ft.ElevatedButton(
            "Refresh",
            icon=ft.Icons.REFRESH,
            on_click=lambda e: show_dashboard(),
            style=ft.ButtonStyle(
                bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                         ft.ControlState.HOVERED: ft.Colors.BLUE},
                color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                       ft.ControlState.HOVERED: ft.Colors.WHITE},
                side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
                      ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
                shape=ft.RoundedRectangleBorder(radius=5)
            )
        )

        content.controls.append(
            ft.Row([refresh_button], alignment=ft.MainAxisAlignment.END)
        )

        def card(title_icon, title, value, icon_color=ft.Colors.BLACK):
            return ft.Container(
                content=ft.Column(
                    [
                        ft.Icon(title_icon, size=40, color=icon_color),
                        ft.Text(title, size=16, color="#333333"),
                        ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color="#000000"),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
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
                width=250,
                height=160,
            )

        content.controls.append(
            ft.Row(
                [
                    card(ft.Icons.PEOPLE, "Total Users", str(total_users)),
                    card(ft.Icons.PERSON, "Active Users", str(active_users), icon_color=ft.Colors.GREEN),
                    card(ft.Icons.HISTORY, "Recent Activities", str(recent_activity_count), icon_color=ft.Colors.BLUE),
                ],
                spacing=20,
                alignment=ft.MainAxisAlignment.CENTER,
            )
        )

        content.controls.append(ft.Text("Recent Users", size=22, weight=ft.FontWeight.BOLD, color="#111111"))

        users_table = ft.DataTable(
            heading_row_color="#FAFAFA",
            columns=[
                ft.DataColumn(ft.Text("Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Email", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
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
                content=ft.Row([users_table], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=PANEL_COLOR,
                border_radius=PANEL_RADIUS,
                padding=20,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            )
        )

        content.controls.append(ft.Text("Recent Activities", size=22, weight=ft.FontWeight.BOLD, color="#111111"))

        user_info = {}
        for email, data in users.items():
            uname = data.get("username")
            if uname:
                team = data.get("team_tags", [])
                team_str = ", ".join(team) if isinstance(team, list) else str(team or "")
                user_info[uname] = {
                    "fullname": data.get("fullname", uname),
                    "email": email,
                    "role": data.get("role", ""),
                    "team": team_str,
                }

        last_10_logs = list(reversed(fresh_logs[-10:]))

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
            rows=[
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(user_info.get(log.get("username", ""), {}).get("fullname", log.get("username", "")))),
                        ft.DataCell(ft.Text(user_info.get(log.get("username", ""), {}).get("email", ""))),
                        ft.DataCell(ft.Text(log.get("username", ""))),
                        ft.DataCell(ft.Text(user_info.get(log.get("username", ""), {}).get("role", ""))),
                        ft.DataCell(ft.Text(user_info.get(log.get("username", ""), {}).get("team", ""))),
                        ft.DataCell(ft.Text(log.get("date", "-"))),
                        ft.DataCell(ft.Text(log.get("activity", ""))),
                    ]
                )
                for log in last_10_logs
            ],
        )

        content.controls.append(
            ft.Container(
                content=ft.Row([activities_table], alignment=ft.MainAxisAlignment.CENTER),
                bgcolor=PANEL_COLOR,
                border_radius=PANEL_RADIUS,
                padding=20,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK)),
            )
        )

        content.update()

    def show_file_approval():
        content.controls.clear()
        try:
            approval_panel = FileApprovalPanel(page, username)
            content.controls.append(approval_panel.create_approval_interface())
        except Exception as e:
            print(f"[ERROR] Failed to load File Approval panel: {e}")
            content.controls.append(ft.Container(content=ft.Text(f"Error loading panel: {e}", color=ft.Colors.RED)))
        content.update()

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
            show_file_approval()
        elif index == 5:
            system_settings(content, username)

    top_nav = create_navbar(username, navigate_to_section, lambda: logout(None))

    page.controls.clear()
    page.add(ft.Column([ft.Container(content=top_nav), ft.Container(content=content, expand=True, padding=20)], spacing=0, expand=True))

    navigate_to_section(initial_tab)

    log_activity(username, "Login")
    save_session(username, "admin")  # will save inside sessions/<username>/session.json
    print(f"[DEBUG] Admin panel initialized for user: {username}")
    page.update()
