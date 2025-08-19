import flet as ft
from flet import FontWeight
import json
import os
from utils.dialog import show_center_sheet
from fpdf import FPDF
import pathlib

USERS_FILE = r"\\KMTI-NAS\Shared\data\users.json"
ACTIVITY_LOGS_FILE = r"\\KMTI-NAS\Shared\data\logs\activity_logs.json"
BACKGROUND = ft.Colors.GREY_100
PANEL_COLOR = "#FFFFFF"
PANEL_RADIUS = 14

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
                # Create role badge
                role = info["role"].upper()
                role_color = {
                                "ADMIN": ft.Colors.RED,
                                "TEAM LEADER": ft.Colors.BLUE,
                                "USER": ft.Colors.GREEN
                            }.get(role, ft.Colors.GREY)

                role_badge = ft.Container(
                    content=ft.Text(role, color=ft.Colors.WHITE, size=10, weight=FontWeight.BOLD),
                    bgcolor=role_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4
                ) if role else ft.Text("", size=14)

                filtered_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(info["fullname"], size=14, weight=FontWeight.BOLD)),
                            ft.DataCell(ft.Text(info["email"], size=14)),
                            ft.DataCell(ft.Text(uname, size=14)),
                            ft.DataCell(role_badge),
                            ft.DataCell(ft.Text(info["team"], size=14)),
                            ft.DataCell(ft.Text(dt_display, size=14)),
                            ft.DataCell(ft.Text(description, size=14)),
                        ]
                    )
                )

        return filtered_rows

    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Full Name", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Email", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Username", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Role", weight=FontWeight.BOLD, size=14), ),
            ft.DataColumn(ft.Text("Team", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Date & Time", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Activity", weight=FontWeight.BOLD, size=14)),
        ],
        rows=build_rows(),
        expand=False,
        data_row_color={ft.ControlState.HOVERED: "#B9B9B9"},
        column_spacing=80,
        horizontal_margin=40,
        data_row_max_height=50,
        data_row_min_height=40,
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
    default_export_dir = pathlib.Path(r"\\KMTI-NAS\Shared\data\export")
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

    # Controls with dashboard styling
    search_field = ft.TextField(
        label="Search / Filter",
        width=300,
        border_radius=10,
        border_color=ft.Colors.GREY_400,
        bgcolor=ft.Colors.WHITE,
        on_change=refresh_table,
    )
    
    export_button = ft.ElevatedButton(
        "Export Logs",
        icon=ft.Icons.UPLOAD_OUTLINED,
        on_click=lambda e: export_logs_action(e),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                     ft.ControlState.HOVERED: ft.Colors.BLUE},
            color={ft.ControlState.DEFAULT: ft.Colors.BLUE,
                   ft.ControlState.HOVERED: ft.Colors.WHITE},
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLUE),
                  ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLUE)},
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    )

    clear_button = ft.ElevatedButton(
        "Clear Filtered",
        icon=ft.Icons.CLEAR_OUTLINED,
        on_click=lambda e: show_center_sheet(
            content.page,
            title="Confirm Delete Filtered Logs",
            message="Are you sure you want to delete these filtered logs? Only filtered logs will be deleted.",
            on_confirm=lambda: clear_logs_action(e),
        ),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                     ft.ControlState.HOVERED: ft.Colors.RED},
            color={ft.ControlState.DEFAULT: ft.Colors.RED,
                   ft.ControlState.HOVERED: ft.Colors.WHITE},
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED),
                  ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    )

    # Top row layout with dashboard styling
    top_controls = ft.Row(
        controls=[
            ft.Text("ACTIVITY LOGS", size=24, weight=FontWeight.BOLD, color="#111111"),
            ft.Container(expand=True),
            search_field,
            export_button,
            clear_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=10
    )

    table_scroll = ft.Row(
        controls=[table],
        scroll=ft.ScrollMode.AUTO,   # ✅ horizontal scroll if needed
        expand=True,
        alignment=ft.MainAxisAlignment.CENTER   # ✅ centers the table
    )

    # Vertical scrollable area
    table_area = ft.ListView(
        controls=[table_scroll],
        expand=True,
        spacing=0,
        padding=0,
        auto_scroll=False
    )

    # Table container with dashboard styling
    table_container = ft.Container(
        content=table_area,
        bgcolor=PANEL_COLOR,
        border_radius=PANEL_RADIUS,
        padding=20,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=1,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        expand=True   # ✅ fills parent while staying centered
    )





    content.controls.extend([
        top_controls,
        ft.Container(height=20),
        table_container
    ])
    content.update()
