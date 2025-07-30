import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os

USERS_FILE = "data/users.json"
ACTIVITY_LOGS_FILE = "data/logs/activity_logs.json"


def load_json(file_path, default):
    """Utility to load JSON safely."""
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r") as f:
            return json.load(f)
    except Exception:
        return default


def activity_logs(content: ft.Column, username: Optional[str]):
    # Clear existing content
    content.controls.clear()

    # Load data
    users = load_json(USERS_FILE, {})
    logs = load_json(ACTIVITY_LOGS_FILE, [])

    # Build user info lookup
    user_info = {}
    for email, data in users.items():
        uname = data.get("username")
        if uname:
            team = data.get("team_tags", [])
            team_str = ", ".join(team) if isinstance(team, list) else (str(team) if team else "")
            user_info[uname] = {
                "fullname": data.get("fullname", uname),
                "email": email,
                "role": data.get("role", ""),
                "team": team_str,
            }

    # Function to build rows from logs with optional filter
    def build_rows(search_text: str = ""):
        filtered_rows = []
        search_text = search_text.lower()

        # Iterate reversed so newest logs appear first
        for log in reversed(logs):
            uname = log.get("username", "")
            info = user_info.get(uname, {
                "fullname": uname,
                "email": "",
                "role": "",
                "team": ""
            })

            dt_display = log.get("date", "-")
            description = log.get("activity", "")

            # Combine all searchable fields
            combined = " ".join([
                info["fullname"],
                info["email"],
                uname,
                info["role"],
                info["team"],
                dt_display,
                description
            ]).lower()

            if search_text in combined:
                filtered_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(info["fullname"])),
                            ft.DataCell(ft.Text(info["email"])),
                            ft.DataCell(ft.Text(uname)),
                            ft.DataCell(ft.Text(info["role"])),
                            ft.DataCell(ft.Text(info["team"])),
                            ft.DataCell(ft.Text(dt_display)),
                            ft.DataCell(ft.Text(description)),
                        ]
                    )
                )

        return filtered_rows

    # DataTable
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Full Name")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Username")),
            ft.DataColumn(ft.Text("Role")),
            ft.DataColumn(ft.Text("Team")),
            ft.DataColumn(ft.Text("Date & Time")),
            ft.DataColumn(ft.Text("Activity")),
        ],
        rows=build_rows(),
        expand=False,
    )

    # Function to refresh table with search text
    def refresh_table(e=None):
        table.rows.clear()
        table.rows.extend(build_rows(search_field.value or ""))
        table.update()

    # Clear logs function
    def clear_logs_action(e):
        if os.path.exists(ACTIVITY_LOGS_FILE):
            with open(ACTIVITY_LOGS_FILE, "w") as f:
                json.dump([], f, indent=4)
        logs.clear()
        refresh_table()

    # Controls
    search_field = ft.TextField(
        label="Search / Filter",
        width=250,
        height=35,
        on_change=refresh_table,
        border_radius=10,
    )
    export_button = ft.ElevatedButton("Export Logs",
                                      style=ft.ButtonStyle(
                                        bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                                ft.ControlState.HOVERED: ft.Colors.GREEN},
                                        color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                            ft.ControlState.HOVERED: ft.Colors.WHITE},
                                        side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                                        shape=ft.RoundedRectangleBorder(radius=5)
                        ))
    clear_button = ft.ElevatedButton("Clear", 
                                     on_click=clear_logs_action,
                                     style=ft.ButtonStyle(
                                        bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                                ft.ControlState.HOVERED: ft.Colors.RED},
                                        color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                            ft.ControlState.HOVERED: ft.Colors.WHITE},
                                        side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
                                        shape=ft.RoundedRectangleBorder(radius=5)
                        ))

    # Top row layout
    top_controls = ft.Row(
        controls=[
            ft.Text("Activity Logs", size=20, weight=FontWeight.BOLD),
            ft.Container(expand=True),  # Stretch
            search_field,
            export_button,
            clear_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    # Center table
    table_container = ft.Container(
        content=ft.Row(
            controls=[table],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        ),
        expand=True,
        padding=40,
    )

    # Add to content
    content.controls.extend([
        top_controls,
        ft.Divider(),
        table_container
    ])
    content.update()
