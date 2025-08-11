import flet as ft
import json
import os
from datetime import datetime
from utils.session_logger import log_logout
from flet import FontWeight, ScrollMode, CrossAxisAlignment, MainAxisAlignment, Colors
from typing import Optional
from admin.navbar import create_navbar
from admin.data_management import data_management
from admin.activity_logs import activity_logs
from admin.system_settings import system_settings
from admin.user_management import user_management
from utils.session_logger import log_activity
from user.user_panel import save_session, clear_session
from admin.components.file_approval_panel import FileApprovalPanel

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

def load_users():
    return load_json(USERS_FILE, {})

def load_logs():
    return load_json(ACTIVITY_LOGS_FILE, [])

def load_metadata():
    return load_json(ACTIVITY_METADATA_FILE, {})

def admin_panel(page: ft.Page, username: Optional[str], initial_tab: int = 0):
    """Enhanced admin panel with hybrid backend integration"""
    
    BACKGROUND = ft.Colors.GREY_100
    PANEL_COLOR = "#FFFFFF"
    PANEL_RADIUS = 14

    page.title = "KMTI Data Management Admin"
    page.vertical_alignment = MainAxisAlignment.START
    page.horizontal_alignment = CrossAxisAlignment.START
    page.bgcolor = BACKGROUND
    page.padding = 0
    page.margin = 0

    # Get hybrid app
    try:
        from main import get_hybrid_app
        hybrid_app = get_hybrid_app(page)
        print(f"🔗 Hybrid app: {'Connected' if hybrid_app else 'Not available'}")
    except Exception as e:
        print(f"⚠️ Could not get hybrid app: {e}")
        hybrid_app = None

    # Get current user info with enhanced team support
    current_user = None
    user_role = "ADMIN"
    user_teams = []
    user_fullname = username

    if hybrid_app:
        try:
            current_user = hybrid_app.get_current_user()
            if current_user:
                user_role = current_user['role']
                user_teams = current_user.get('team_tags', [])
                user_fullname = current_user.get('fullname', username)
                print(f"👤 Hybrid User: {user_fullname} ({user_role}) Teams: {user_teams}")
        except Exception as e:
            print(f"⚠️ Error getting current user from hybrid: {e}")
    else:
        # Enhanced legacy user lookup
        try:
            legacy_users = load_users()
            for email, user_data in legacy_users.items():
                if user_data['username'] == username:
                    user_role = user_data.get('role', 'ADMIN')
                    user_teams = user_data.get('team_tags', [])
                    user_fullname = user_data.get('fullname', username)
                    print(f"👤 Legacy User: {user_fullname} ({user_role}) Teams: {user_teams}")
                    break
        except Exception as e:
            print(f"⚠️ Legacy user lookup error: {e}")

    def logout(e):
        """Enhanced logout with hybrid support"""
        print(f"[DEBUG] logout() called by username={username}")
        
        try:
            # Hybrid logout
            if hybrid_app:
                hybrid_app.logout()
                print("✅ Hybrid logout completed")
            else:
                # Legacy logout
                log_logout(username, "admin")
                clear_session()
                print("✅ Legacy logout completed")
            
            # Always log activity using existing logger
            log_activity(username, "Logout")
            
            page.clean()
            from login_window import login_view
            login_view(page)
            
        except Exception as error:
            print(f"❌ Logout error: {error}")
            # Force logout anyway
            from login_window import login_view
            login_view(page)

    content = ft.Column(
        scroll=ScrollMode.AUTO,
        expand=True,
        spacing=20,
        horizontal_alignment=CrossAxisAlignment.CENTER,
    )

    # --- Enhanced utility functions with proper logging ---

    def get_last_activity_entry(username_lookup: str):
        """Get last activity using existing session_logger"""
        fresh_logs = load_logs()
        for entry in reversed(fresh_logs):
            if entry.get("username") == username_lookup:
                return entry
        return None

    def is_user_online(user_data) -> bool:
        """Check if user is online using existing session system"""
        uname = user_data.get("username")
        if not uname:
            return False
        
        # Check hybrid first, then fallback to legacy
        if hybrid_app:
            try:
                # Check if hybrid has session management
                if hasattr(hybrid_app, 'user_service'):
                    users = hybrid_app.user_service.get_users()
                    for user in users:
                        if user.get('username') == uname:
                            return user.get('is_online', False)
            except Exception:
                pass
        
        # Legacy check using activity logs
        last_entry = get_last_activity_entry(uname)
        if not last_entry:
            return False
        return last_entry.get("activity") == "Login"

    def get_login_status(user_email, user_data):
        online = is_user_online(user_data)
        return ft.Text(
            "Online" if online else "Offline",
            color=Colors.GREEN if online else Colors.RED,
            weight=FontWeight.BOLD
        )

    def show_dashboard():
        """Enhanced dashboard with proper logging integration"""
        content.controls.clear()

        # Load data from hybrid or legacy
        total_users = 0
        active_users = 0
        recent_activity_count = 0
        users = {}
        fresh_logs = []

        if hybrid_app:
            try:
                # Get hybrid data
                all_users = hybrid_app.user_service.get_users()
                total_users = len(all_users)
                
                # Convert to legacy format for compatibility
                for user in all_users:
                    users[user['email']] = {
                        'fullname': user.get('fullname', ''),
                        'username': user.get('username', ''),
                        'role': user.get('role', ''),
                        'team_tags': user.get('team_tags', [])
                    }
                
                # Use existing activity logs instead of non-existent activity_service
                fresh_logs = load_logs()
                recent_activity_count = len(fresh_logs)
                
                # Count active users
                active_users = sum(1 for u in users.values() if is_user_online(u))
                
                print(f"📊 Hybrid Dashboard: {total_users} users, {active_users} active, {recent_activity_count} activities")
                
            except Exception as e:
                print(f"⚠️ Error loading hybrid dashboard data: {e}")
                # Fallback to legacy
                users = load_users()
                fresh_logs = load_logs()
                total_users = len(users)
                active_users = sum(1 for u in users.values() if is_user_online(u))
                recent_activity_count = len(fresh_logs)
        else:
            # Legacy data loading
            users = load_users()
            fresh_logs = load_logs()
            total_users = len(users)
            active_users = sum(1 for u in users.values() if is_user_online(u))
            recent_activity_count = len(fresh_logs)
            print(f"📊 Legacy Dashboard: {total_users} users, {active_users} active, {recent_activity_count} activities")

        # Sort logs by datetime for reliable "most recent"
        def parse_datetime(log):
            try:
                date_str = log.get("date", log.get("timestamp", ""))
                if "T" in date_str:  # ISO format from hybrid
                    return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:  # Legacy format
                    return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
            except Exception:
                return datetime.min

        fresh_logs.sort(key=parse_datetime, reverse=True)

        # Add title with Refresh button
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

        # System status indicator
        system_status = ft.Container(
            content=ft.Row([
                ft.Icon(
                    ft.Icons.CLOUD_DONE if hybrid_app else ft.Icons.FOLDER, 
                    color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                    size=16
                ),
                ft.Text(
                    "NAS Connected" if hybrid_app else "Legacy Mode",
                    size=12,
                    color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                    weight=FontWeight.BOLD
                )
            ], spacing=5),
            bgcolor=ft.Colors.GREEN_100 if hybrid_app else ft.Colors.ORANGE_100,
            padding=ft.padding.symmetric(horizontal=10, vertical=5),
            border_radius=10
        )

        content.controls.append(
            ft.Row(
                [
                    system_status,
                    ft.Container(expand=True),
                    refresh_button,
                ],
                alignment=MainAxisAlignment.SPACE_BETWEEN,
            )
        )

        # --- Small metric cards ---
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
                width=250,
                height=160,
            )

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

        # --- Recent Users Table ---
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

        # --- Recent Activities Section ---
        content.controls.append(
            ft.Text("Recent Activities", size=22, weight=FontWeight.BOLD, color="#111111")
        )

        # Build user_info lookup (compatible with both hybrid and legacy)
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

        # Only the latest 10 logs
        last_10_logs = fresh_logs[:10]

        rows = []
        for log in last_10_logs:
            uname = log.get("username", "")
            info = user_info.get(
                uname,
                {"fullname": uname, "email": "", "role": "", "team": ""},
            )
            
            # Handle both hybrid and legacy date formats
            log_date = log.get("date", log.get("timestamp", "-"))
            if "T" in log_date:  # ISO format from hybrid
                try:
                    dt = datetime.fromisoformat(log_date.replace('Z', '+00:00'))
                    log_date = dt.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    pass
            
            rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Text(info["fullname"])),
                        ft.DataCell(ft.Text(info["email"])),
                        ft.DataCell(ft.Text(uname)),
                        ft.DataCell(ft.Text(info["role"])),
                        ft.DataCell(ft.Text(info["team"])),
                        ft.DataCell(ft.Text(log_date)),
                        ft.DataCell(ft.Text(log.get("activity", log.get("action", "")))),
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

    def show_file_approval():
        """Enhanced File Approval panel with hybrid support"""
        content.controls.clear()
        try:
            # Create file approval panel with hybrid support but without non-existent services
            approval_panel = FileApprovalPanel(page, username, hybrid_app=hybrid_app)
            approval_interface = approval_panel.create_approval_interface()
            content.controls.append(approval_interface)
            content.update()
        except Exception as e:
            print(f"[ERROR] Failed to load File Approval panel: {e}")
            content.controls.append(
                ft.Container(
                    content=ft.Column([
                        ft.Text("File Approval Panel", size=24, weight=ft.FontWeight.BOLD),
                        ft.Text(f"Error loading panel: {e}", color=ft.Colors.RED),
                        ft.ElevatedButton("Refresh", on_click=lambda e: show_file_approval())
                    ]),
                    padding=20
                )
            )
            content.update()

    def navigate_to_section(index: int):
        """Fixed navigation with correct function signatures"""
        content.controls.clear()
        
        if index == 0:
            show_dashboard()
        elif index == 1:
            data_management(content, username)
        elif index == 2:
            # Fixed: Pass only the required 2 arguments
            user_management(content, username) 
        elif index == 3:
            activity_logs(content, username)
        elif index == 4:  
            show_file_approval()    
        elif index == 5: 
            system_settings(content, username)

    # Create navbar (unchanged)
    top_nav = create_navbar(username, navigate_to_section, lambda: logout(None))

    page.controls.clear()

    page.add(
        ft.Column(
            [
                ft.Container(
                    content=top_nav,
                    padding=0,
                    margin=0,
                ),
                ft.Container(
                    content=content,
                    expand=True,
                    padding=20,
                ),
            ],
            spacing=0,
            expand=True,
        )
    )

    navigate_to_section(initial_tab)

    # Enhanced session and activity logging using existing system
    try:
        # Use existing session_logger instead of non-existent activity_service
        log_activity(username, "Login")
        save_session(username, "admin")
        
    except Exception as e:
        print(f"⚠️ Error logging activity: {e}")

    print(f"[DEBUG] Admin panel initialized for user: {username} ({'Hybrid' if hybrid_app else 'Legacy'} mode)")
    page.update()