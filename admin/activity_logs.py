import flet as ft
from flet import FontWeight
import json
import os
from utils.dialog import show_center_sheet
from fpdf import FPDF
import pathlib

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


def activity_logs(content: ft.Column, username: str):
    # Clear previous content
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

    # Function to clear only filtered logs
    def clear_logs_action(e):
        search_text = (search_field.value or "").lower()
        print(f"[DEBUG] clear_logs_action called with filter: '{search_text}'")

        if not search_text:
            print("[DEBUG] No filter applied, nothing to delete.")
            return

        remaining_logs = []
        for log in logs:
            uname = log.get("username", "")
            info = user_info.get(uname, {
                "fullname": uname,
                "email": "",
                "role": "",
                "team": ""
            })
            dt_display = log.get("date", "-")
            description = log.get("activity", "")
            combined = " ".join([
                info["fullname"],
                info["email"],
                uname,
                info["role"],
                info["team"],
                dt_display,
                description
            ]).lower()

            if search_text not in combined:
                remaining_logs.append(log)

        with open(ACTIVITY_LOGS_FILE, "w") as f:
            json.dump(remaining_logs, f, indent=4)

        logs.clear()
        logs.extend(remaining_logs)
        refresh_table()

    # Ensure default export directory
    default_export_dir = pathlib.Path("data/export")
    default_export_dir.mkdir(parents=True, exist_ok=True)

    # File picker (still appended in case needed later)
    file_picker = ft.FilePicker()
    content.page.overlay.append(file_picker)

    # Function to export logs to PDF
    def export_logs_action(e):
        search_text = (search_field.value or "").lower()
        print(f"[DEBUG] export_logs_action called with filter: '{search_text}'")

        filtered = []
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
                filtered.append({
                    "fullname": info["fullname"],
                    "email": info["email"],
                    "username": uname,
                    "role": info["role"],
                    "team": info["team"],
                    "date": dt_display,
                    "activity": description
                })

        if not filtered:
            print("[DEBUG] No logs found to export.")
            return

        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", size=12)
        pdf.cell(200, 10, txt="Exported Activity Logs", ln=True, align="C")
        pdf.ln(5)

        headers = ["Full Name", "Email", "Username", "Role", "Team", "Date & Time", "Activity"]
        header_line = " | ".join(headers)
        pdf.multi_cell(0, 8, header_line)
        pdf.ln(2)

        for entry in filtered:
            line = f"{entry['fullname']} | {entry['email']} | {entry['username']} | {entry['role']} | {entry['team']} | {entry['date']} | {entry['activity']}"
            pdf.multi_cell(0, 8, line)
            pdf.ln(1)

        # Find a unique filename
        base_filename = "exported_logs"
        ext = ".pdf"
        counter = 0
        export_file = default_export_dir / f"{base_filename}{ext}"
        while export_file.exists():
            counter += 1
            export_file = default_export_dir / f"{base_filename}_{counter}{ext}"

        pdf.output(str(export_file))
        print(f"[DEBUG] Logs exported to {export_file}")

    # Controls
    search_field = ft.TextField(
        label="Search / Filter",
        width=250,
        height=40,
        on_change=refresh_table,
        border_radius=10,
    )
    export_button = ft.ElevatedButton(
        "Export Logs",
        icon=ft.Icons.UPLOAD_OUTLINED,
        on_click=lambda e: export_logs_action(e),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                     ft.ControlState.HOVERED: ft.Colors.GREEN},
            color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                   ft.ControlState.HOVERED: ft.Colors.WHITE},
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN),
                  ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
            shape=ft.RoundedRectangleBorder(radius=5)
        )
    )

    clear_button = ft.ElevatedButton(
        "Clear",
        icon=ft.Icons.CLEAR_OUTLINED,
        on_click=lambda e: show_center_sheet(
            content.page,
            title="Confirm Delete Filtered Logs",
            message="Are you sure you want to delete this filtered logs? Only filtered logs will be deleted",
            on_confirm=lambda: clear_logs_action(e),
        ),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                    ft.ControlState.HOVERED: ft.Colors.RED},
            color={ft.ControlState.DEFAULT: ft.Colors.RED,
                ft.ControlState.HOVERED: ft.Colors.WHITE},
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED),
                ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
            shape=ft.RoundedRectangleBorder(radius=5)
        )
    )

    # Top row layout
    top_controls = ft.Row(
        controls=[
            ft.Text("Activity Logs", size=22, weight=FontWeight.BOLD),
            ft.Container(expand=True),
            search_field,
            export_button,
            clear_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    table_container = ft.Container(
        content=ft.Row(
            controls=[table],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        ),
        expand=True,
        padding=10,
    )

    content.controls.extend([
        top_controls,
        ft.Divider(),
        table_container
    ])
    content.update()
