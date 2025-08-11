import flet as ft
from flet import FontWeight
import json
import os
from utils.dialog import show_center_sheet
from fpdf import FPDF
import pathlib

USERS_FILE = "data/users.json"
ACTIVITY_LOGS_FILE = "data/logs/activity_logs.json"
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
    """Enhanced activity logs using existing session_logger system"""
    content.controls.clear()

    # Get hybrid app if available
    try:
        from main import get_hybrid_app
        hybrid_app = get_hybrid_app(content.page)
    except Exception as e:
        print(f"⚠️ Could not get hybrid app: {e}")
        hybrid_app = None

    def load_users():
        """Load users from hybrid or legacy system"""
        if hybrid_app:
            try:
                # Get users from hybrid backend
                hybrid_users = hybrid_app.user_service.get_users()
                
                # Convert to legacy format for compatibility
                users = {}
                for user in hybrid_users:
                    users[user['email']] = {
                        'fullname': user.get('fullname', ''),
                        'username': user.get('username', ''),
                        'role': user.get('role', 'USER'),
                        'team_tags': user.get('team_tags', [])
                    }
                
                print(f"👥 Hybrid: Loaded {len(users)} users for activity logs")
                return users
                
            except Exception as e:
                print(f"⚠️ Error loading hybrid users for logs: {e}")
        
        # Fallback to legacy
        users = load_json(USERS_FILE, {})
        print(f"👥 Legacy: Loaded {len(users)} users for activity logs")
        return users

    def load_logs():
        """Load activity logs from existing JSON system (no hybrid service)"""
        # Always use existing activity logs since activity_service doesn't exist
        logs = load_json(ACTIVITY_LOGS_FILE, [])
        print(f"📋 Activity Logs: Loaded {len(logs)} from existing session logger")
        return logs

    def save_logs(logs):
        """Save logs using existing system"""
        with open(ACTIVITY_LOGS_FILE, "w") as f:
            json.dump(logs, f, indent=4)
        print("✅ Activity logs saved to JSON")

    # Load data
    users = load_users()
    logs = load_logs()

    # System status header
    system_status = ft.Container(
        content=ft.Row([
            ft.Icon(
                ft.Icons.CLOUD_DONE if hybrid_app else ft.Icons.FOLDER, 
                color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                size=16
            ),
            ft.Text(
                f"{'Hybrid Users + Legacy Logs' if hybrid_app else 'Legacy System'} - {len(logs)} activities",
                size=12,
                color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                weight=ft.FontWeight.BOLD
            )
        ], spacing=5),
        bgcolor=ft.Colors.GREEN_100 if hybrid_app else ft.Colors.ORANGE_100,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=10,
        margin=ft.margin.only(bottom=15)
    )

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

        # Sort logs by date (newest first) - all from existing JSON system
        def parse_datetime(log):
            date_str = log.get("date", "")
            try:
                # Only handle legacy format since we're using existing logs
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except:
                return datetime.min

        from datetime import datetime
        sorted_logs = sorted(logs, key=parse_datetime, reverse=True)

        # Filter logs
        for log in sorted_logs:
            uname = log.get("username", "")
            info = user_info.get(uname, {
                "fullname": uname,
                "email": "",
                "role": "",
                "team": ""
            })

            dt_display = log.get("date", "-")
            description = log.get("activity", "")
            details = log.get("details", "")

            # Combine all searchable fields
            combined = " ".join([
                info["fullname"],
                info["email"],
                uname,
                info["role"],
                info["team"],
                dt_display,
                description,
                details
            ]).lower()

            if search_text in combined:
                # Create role badge
                role = info["role"].upper()
                if role == "ADMIN":
                    role_color = ft.Colors.RED
                elif role == "TEAM_LEADER":
                    role_color = ft.Colors.BLUE
                else:
                    role_color = ft.Colors.GREEN
                    
                role_badge = ft.Container(
                    content=ft.Text(role, color=ft.Colors.WHITE, size=10, weight=FontWeight.BOLD),
                    bgcolor=role_color,
                    padding=ft.padding.symmetric(horizontal=8, vertical=4),
                    border_radius=4
                ) if role else ft.Text("", size=14)

                # Activity icon based on action type
                activity_lower = description.lower()
                if 'login' in activity_lower:
                    activity_icon = ft.Icon(ft.Icons.LOGIN, size=16, color=ft.Colors.GREEN)
                elif 'logout' in activity_lower:
                    activity_icon = ft.Icon(ft.Icons.LOGOUT, size=16, color=ft.Colors.GREY)
                elif 'approve' in activity_lower:
                    activity_icon = ft.Icon(ft.Icons.CHECK_CIRCLE, size=16, color=ft.Colors.GREEN)
                elif 'reject' in activity_lower:
                    activity_icon = ft.Icon(ft.Icons.CANCEL, size=16, color=ft.Colors.RED)
                elif 'upload' in activity_lower or 'file' in activity_lower:
                    activity_icon = ft.Icon(ft.Icons.UPLOAD_FILE, size=16, color=ft.Colors.BLUE)
                elif 'user' in activity_lower:
                    activity_icon = ft.Icon(ft.Icons.PERSON, size=16, color=ft.Colors.PURPLE)
                else:
                    activity_icon = ft.Icon(ft.Icons.INFO, size=16, color=ft.Colors.GREY)

                # Format activity with icon
                activity_with_icon = ft.Row([
                    activity_icon,
                    ft.Text(description, size=14)
                ], spacing=8)

                filtered_rows.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(info["fullname"], size=14, weight=FontWeight.BOLD)),
                            ft.DataCell(ft.Text(info["email"], size=14)),
                            ft.DataCell(ft.Text(uname, size=14)),
                            ft.DataCell(role_badge),
                            ft.DataCell(ft.Text(info["team"], size=14)),
                            ft.DataCell(ft.Text(dt_display, size=14)),
                            ft.DataCell(activity_with_icon),
                        ]
                    )
                )

        return filtered_rows

    # DataTable with enhanced styling
    table = ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text("Full Name", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Email", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Username", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Role", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Team", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Date & Time", weight=FontWeight.BOLD, size=14)),
            ft.DataColumn(ft.Text("Activity", weight=FontWeight.BOLD, size=14)),
        ],
        rows=build_rows(),
        expand=False,
        heading_row_color="#FAFAFA",
        data_row_color={ft.ControlState.HOVERED: "#E3F2FD"},
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

    # Function to clear filtered logs
    def clear_logs_action(e):
        search_text = (search_field.value or "").lower()
        print(f"[DEBUG] clear_logs_action called with filter: '{search_text}'")

        if not search_text:
            print("[DEBUG] No filter applied, nothing to delete.")
            return

        # Clear filtered logs from existing JSON system
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

        save_logs(remaining_logs)
        logs.clear()
        logs.extend(remaining_logs)

        refresh_table()

    # Ensure default export directory
    default_export_dir = pathlib.Path("data/export")
    default_export_dir.mkdir(parents=True, exist_ok=True)

    # Function to export logs to PDF
    def export_logs_action(e):
        search_text = (search_field.value or "").lower()
        print(f"[DEBUG] export_logs_action called with filter: '{search_text}'")

        filtered = []
        
        # Sort logs by date
        def parse_datetime(log):
            date_str = log.get("date", "")
            try:
                from datetime import datetime
                return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except:
                return datetime.min

        sorted_logs = sorted(logs, key=parse_datetime, reverse=True)
        
        for log in sorted_logs:
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

        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", size=12)
            pdf.cell(200, 10, txt=f"KMTI Activity Logs Export", ln=True, align="C")
            pdf.ln(2)
            pdf.set_font("Arial", size=10)
            
            from datetime import datetime
            pdf.cell(200, 8, txt=f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", ln=True, align="C")
            pdf.cell(200, 8, txt=f"System: {'Hybrid Users + Legacy Logs' if hybrid_app else 'Legacy System'}", ln=True, align="C")
            pdf.cell(200, 8, txt=f"Total Records: {len(filtered)}", ln=True, align="C")
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
            base_filename = "kmti_activity_logs"
            ext = ".pdf"
            counter = 0
            export_file = default_export_dir / f"{base_filename}{ext}"
            while export_file.exists():
                counter += 1
                export_file = default_export_dir / f"{base_filename}_{counter}{ext}"

            pdf.output(str(export_file))
            print(f"[DEBUG] Logs exported to {export_file}")
            
            # Show success message
            content.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Logs exported to {export_file.name}"),
                bgcolor=ft.Colors.GREEN,
                duration=5000
            )
            content.page.snack_bar.open = True
            content.page.update()
            
        except Exception as e:
            print(f"❌ Error exporting logs: {e}")
            content.page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Export failed: {str(e)}"),
                bgcolor=ft.Colors.RED,
                duration=5000
            )
            content.page.snack_bar.open = True
            content.page.update()

    # Controls with enhanced styling
    search_field = ft.TextField(
        label="Search / Filter Activities",
        width=350,
        border_radius=10,
        border_color=ft.Colors.GREY_400,
        bgcolor=ft.Colors.WHITE,
        on_change=refresh_table,
        prefix_icon=ft.Icons.SEARCH
    )
    
    export_button = ft.ElevatedButton(
        "Export PDF",
        icon=ft.Icons.PICTURE_AS_PDF,
        on_click=export_logs_action,
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
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
        icon=ft.Icons.DELETE_SWEEP,
        on_click=lambda e: show_center_sheet(
            content.page,
            title="Confirm Delete Filtered Logs",
            message=f"Are you sure you want to delete filtered logs?\n\nFiltered activities will be removed from local activity log files.",
            on_confirm=lambda: clear_logs_action(e),
        ),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                     ft.ControlState.HOVERED: ft.Colors.RED},
            color={ft.ControlState.DEFAULT: ft.Colors.RED,
                   ft.ControlState.HOVERED: ft.Colors.WHITE},
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED),
                  ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    )

    refresh_button = ft.ElevatedButton(
        "Refresh",
        icon=ft.Icons.REFRESH,
        on_click=lambda e: activity_logs(content, username),
        style=ft.ButtonStyle(
            bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                     ft.ControlState.HOVERED: ft.Colors.GREEN},
            color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                   ft.ControlState.HOVERED: ft.Colors.WHITE},
            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN),
                  ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
            shape=ft.RoundedRectangleBorder(radius=8)
        )
    )

    # Top row layout with enhanced styling
    top_controls = ft.Row(
        controls=[
            ft.Text("Activity Logs", size=22, weight=FontWeight.BOLD, color="#111111"),
            ft.Container(expand=True),
            search_field,
            refresh_button,
            export_button,
            clear_button,
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
        spacing=10
    )

    # Table container with enhanced styling
    table_container = ft.Container(
        content=ft.Column([
            table
        ], expand=True, scroll=ft.ScrollMode.AUTO),
        bgcolor=PANEL_COLOR,
        border_radius=PANEL_RADIUS,
        padding=20,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=1,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        expand=True
    )

    content.controls.extend([
        system_status,
        top_controls,
        ft.Container(height=20),
        table_container
    ])
    content.update()