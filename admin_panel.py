# admin_panel.py

import flet as ft
import json
import os
from datetime import datetime
from typing import Optional

from utils.session_logger import log_logout, log_activity
from user.user_panel import save_session, clear_session
from admin.navbar import create_navbar
from admin.data_management import data_management
from admin.activity_logs import activity_logs
from admin.system_settings import system_settings
from admin.user_management import user_management
from admin.components.file_approval_panel import FileApprovalPanel
from utils.approval import get_pending_files, approve_file, reject_file

USERS_FILE = "data/users.json"
ACTIVITY_LOGS_FILE = "data/logs/activity_logs.json"


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


def admin_panel(page: ft.Page, username: Optional[str], initial_tab: int = 0):
    BACKGROUND = ft.Colors.GREY_100
    PANEL_COLOR = "#FFFFFF"
    PANEL_RADIUS = 14

    page.title = "KMTI Admin Panel"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.margin = 0

    def logout(e):
        log_logout(username, "admin")
        log_activity(username, "Logout")
        clear_session()
        page.clean()
        from login_window import login_view
        login_view(page)

    content = ft.Column(
        scroll=ft.ScrollMode.AUTO,
        expand=True,
        spacing=20,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    def get_last_activity_entry(uname: str):
        logs = load_logs()
        for entry in reversed(logs):
            if entry.get("username") == uname:
                return entry
        return None

    def is_user_online(user_data):
        uname = user_data.get("username")
        last_entry = get_last_activity_entry(uname)
        return last_entry and last_entry.get("activity") == "Login"

    def get_login_status(email, user_data):
        return ft.Text(
            "Online" if is_user_online(user_data) else "Offline",
            color=ft.Colors.GREEN if is_user_online(user_data) else ft.Colors.RED,
            weight=ft.FontWeight.BOLD
        )

    def show_dashboard():
        content.controls.clear()
        users = load_users()
        logs = load_logs()

        logs.sort(key=lambda x: datetime.strptime(x.get("date", ""), "%Y-%m-%d %H:%M:%S") if x.get("date") else datetime.min)

        total_users = len(users)
        active_users = sum(1 for u in users.values() if is_user_online(u))
        recent_activity_count = len(logs)

        refresh_btn = ft.ElevatedButton(
            "Refresh",
            icon=ft.Icons.REFRESH,
            on_click=lambda e: show_dashboard()
        )

        def card(icon, title, value, icon_color=ft.Colors.BLACK):
            return ft.Container(
                content=ft.Column([
                    ft.Icon(icon, size=40, color=icon_color),
                    ft.Text(title),
                    ft.Text(str(value), size=26, weight=ft.FontWeight.BOLD),
                ], spacing=6, horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                bgcolor=PANEL_COLOR,
                padding=20,
                width=250,
                border_radius=PANEL_RADIUS,
                shadow=ft.BoxShadow(blur_radius=8, spread_radius=1, color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK))
            )

        content.controls.append(ft.Row([refresh_btn], alignment=ft.MainAxisAlignment.END))
        content.controls.append(
            ft.Row([
                card(ft.Icons.PEOPLE, "Total Users", total_users),
                card(ft.Icons.PERSON, "Active Users", active_users, ft.Colors.GREEN),
                card(ft.Icons.HISTORY, "Activity Logs", recent_activity_count, ft.Colors.BLUE),
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=20)
        )

        # User table
        user_table = ft.DataTable(
            heading_row_color="#FAFAFA",
            columns=[
                ft.DataColumn(ft.Text("Name", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Email", weight=ft.FontWeight.BOLD)),
                ft.DataColumn(ft.Text("Status", weight=ft.FontWeight.BOLD)),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(u.get("fullname", ""))),
                    ft.DataCell(ft.Text(email)),
                    ft.DataCell(get_login_status(email, u)),
                ])
                for email, u in list(users.items())[:5]
            ]
        )

        content.controls.append(
            ft.Container(user_table, bgcolor=PANEL_COLOR, padding=20, border_radius=PANEL_RADIUS)
        )

        # Activity Logs
        recent_logs = list(reversed(logs[-10:]))
        user_lookup = {
            u.get("username"): {
                "fullname": u.get("fullname"),
                "email": email,
                "role": u.get("role"),
                "team": ", ".join(u.get("team_tags", [])) if isinstance(u.get("team_tags"), list) else ""
            }
            for email, u in users.items()
        }

        log_table = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Full Name")),
                ft.DataColumn(ft.Text("Email")),
                ft.DataColumn(ft.Text("Username")),
                ft.DataColumn(ft.Text("Role")),
                ft.DataColumn(ft.Text("Team")),
                ft.DataColumn(ft.Text("Date")),
                ft.DataColumn(ft.Text("Activity")),
            ],
            rows=[
                ft.DataRow(cells=[
                    ft.DataCell(ft.Text(user_lookup.get(log.get("username"), {}).get("fullname", "-"))),
                    ft.DataCell(ft.Text(user_lookup.get(log.get("username"), {}).get("email", "-"))),
                    ft.DataCell(ft.Text(log.get("username"))),
                    ft.DataCell(ft.Text(user_lookup.get(log.get("username"), {}).get("role", "-"))),
                    ft.DataCell(ft.Text(user_lookup.get(log.get("username"), {}).get("team", "-"))),
                    ft.DataCell(ft.Text(log.get("date", "-"))),
                    ft.DataCell(ft.Text(log.get("activity", "-"))),
                ])
                for log in recent_logs
            ]
        )

        content.controls.append(
            ft.Container(log_table, bgcolor=PANEL_COLOR, padding=20, border_radius=PANEL_RADIUS)
        )
        content.update()

    def review_panel():
        content.controls.clear()
        metadata = load_metadata()
        pending_files = [fname for fname, meta in metadata.items() if meta.get("status") == "pending"]

        for fname in pending_files:
            meta = metadata[fname]
            comment_field = ft.TextField(label="Comment", multiline=True, width=400, height=60)

            content.controls.append(
                ft.Card(
                    content=ft.Column([
                        ft.Text(f"📄 {fname}", size=18, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Owner: {meta.get('owner')}"),
                        comment_field,
                        ft.Row([
                            ft.ElevatedButton("✅ Approve", on_click=lambda e, f=fname, c=comment_field: approve_file(f, "admin", c.value)),
                            ft.ElevatedButton("❌ Reject", on_click=lambda e, f=fname, c=comment_field: reject_file(f, "admin", c.value)),
                        ])
                    ])
                )
            )
        content.update()

    def show_file_approvals():
        # Initialize the file approval panel
        approval_panel = FileApprovalPanel(page, username)
        
        # Clear and update content
        content.controls.clear()
        content.controls.append(approval_panel.build())
        content.update()

    def navigate_to_section(index: int):
        content.controls.clear()
        if index == 0:
            show_dashboard()
        elif index == 1:
            show_file_approvals()
        elif index == 2:
            data_management(content, username)
        elif index == 3:
            user_management(content, username)
        elif index == 4:
            activity_logs(content, username)
        elif index == 5:
            system_settings(content, username)
        elif index == 5:
            review_panel()

    top_nav = create_navbar(username, navigate_to_section, lambda: logout(None))

    page.controls.clear()
    page.add(
        ft.Column([
            ft.Container(content=top_nav),
            ft.Container(content=content, expand=True, padding=20),
        ], spacing=0, expand=True)
    )

    navigate_to_section(initial_tab)

    log_activity(username, "Login")
    save_session(username, "admin")
    page.update()
    print(f"[DEBUG] Admin panel initialized for user: {username}")
