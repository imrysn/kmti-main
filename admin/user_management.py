import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
import hashlib
import asyncio
from datetime import datetime
from admin.utils.team_utils import get_team_options
from utils.session_logger import get_active_sessions, get_last_runtime, log_activity
from utils.dialog import show_center_sheet

def user_management(content: ft.Column, username: Optional[str]):
    """Enhanced user management with hybrid backend support using existing add_user.py and reset_password.py"""
    content.controls.clear()

    # Get hybrid app if available
    try:
        from main import get_hybrid_app
        hybrid_app = get_hybrid_app(content.page)
        print(f"🔗 User Management: {'Hybrid' if hybrid_app else 'Legacy'} mode")
    except Exception as e:
        print(f"⚠️ Could not get hybrid app: {e}")
        hybrid_app = None

    users_file = "data/users.json"
    edit_mode = {"value": False}
    filter_mode = {"value": "All"}
    runtime_labels = {}

    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def migrate_plain_passwords(users):
        changed = False
        for email, data in users.items():
            pw = data.get("password", "")
            if len(pw) != 64 or not all(c in "0123456789abcdef" for c in pw.lower()):
                data["password"] = hash_password(pw)
                changed = True
        return changed

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
                        'password': user.get('password', ''),  # Already hashed in hybrid
                        'role': user.get('role', 'USER'),
                        'team_tags': user.get('team_tags', []),
                        'join_date': user.get('created_at', ''),
                        'last_login': user.get('last_login', '')
                    }
                
                print(f"👥 Hybrid: Retrieved {len(users)} users")
                return users
                
            except Exception as e:
                print(f"⚠️ Error loading hybrid users: {e}")
        
        # Fallback to legacy
        if not os.path.exists(users_file):
            return {}
        
        with open(users_file, "r") as f:
            users = json.load(f)
        
        # Migrate plain passwords if needed
        if migrate_plain_passwords(users):
            save_users(users)
        
        print(f"👥 Legacy: Retrieved {len(users)} users")
        return users

    def save_users(data):
        """Save users to hybrid or legacy system"""
        if hybrid_app:
            try:
                # Update users in hybrid backend
                for email, user_data in data.items():
                    hybrid_app.user_service.update_user(email, user_data)
                print("✅ Hybrid: Users saved")
                return
            except Exception as e:
                print(f"⚠️ Error saving to hybrid: {e}")
        
        # Fallback to legacy
        with open(users_file, "w") as f:
            json.dump(data, f, indent=4)
        print("✅ Legacy: Users saved")

    users = load_users()

    # System status header
    system_status = ft.Container(
        content=ft.Row([
            ft.Icon(
                ft.Icons.CLOUD_DONE if hybrid_app else ft.Icons.FOLDER, 
                color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                size=16
            ),
            ft.Text(
                f"{'NAS Database' if hybrid_app else 'Legacy Files'} - {len(users)} users",
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

    search_field = ft.TextField(
        label="Search users...",
        expand=False,
        width=400,
        border_radius=10,
        border_color=ft.Colors.GREY,
        on_change=lambda e: refresh_table()
    )

    filter_dropdown = ft.Dropdown(
        label="Filter / Sort",
        expand=False,
        width=180,
        border_radius=10,
        value="All",
        options=[
            ft.dropdown.Option("All"),
            ft.dropdown.Option("Sort by Name (A–Z)"),
            ft.dropdown.Option("Sort by Email (A–Z)"),
            ft.dropdown.Option("Sort by Username (A–Z)"),
            ft.dropdown.Option("Filter by Role (ADMIN)"),
            ft.dropdown.Option("Filter by Role (USER)"),
            ft.dropdown.Option("Filter by Role (TEAM_LEADER)"),
            ft.dropdown.Option("Filter by Team"),
        ],
        on_change=lambda e: apply_filter(e.control.value)
    )

    all_columns = [
        ("Full Name", True),
        ("Email", True),
        ("Username", True),
        ("Password", True),
        ("Role", True),
        ("Team", True),
        ("Runtime", True),
        ("Remove User", True),
    ]

    table = ft.DataTable(
        expand=True,
        columns=[],
        rows=[]
    )

    def refresh_columns_for_width(width: int):
        table.columns.clear()

        show_password = width >= 1000
        show_team = width >= 1000

        for col_name, always in all_columns:
            if col_name == "Password" and not show_password:
                continue
            if col_name == "Team" and not show_team:
                continue
            table.columns.append(ft.DataColumn(ft.Text(col_name)))

        # Adjust row size
        if width > 1200:
            table.heading_row_height = 60
            table.data_row_min_height = 60
        elif width > 800:
            table.heading_row_height = 50
            table.data_row_min_height = 50
        else:
            table.heading_row_height = 40
            table.data_row_min_height = 40

    def refresh_team_options():
        """Get team options from existing teams.json (no hybrid service call)"""
        try:
            # Always use existing team_utils since team_service doesn't exist
            team_options = get_team_options()
            return [ft.dropdown.Option(opt) for opt in team_options]
        except Exception as e:
            print(f"⚠️ Error getting team options: {e}")
            # Return default teams
            default_teams = ["Minatogumi", "SOLID WORKS", "WINDSMILE", "AGCC Project", "KMTI PJ", "KUSAKABE", "ADMIN", "IT"]
            return [ft.dropdown.Option(opt) for opt in default_teams]

    def apply_filter(value: str):
        filter_mode["value"] = value
        refresh_table()

    def format_runtime_from_delta(delta):
        total_seconds = int(delta.total_seconds())
        days, rem = divmod(total_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        return f"{days}d {hours}h {minutes}m {seconds}s"

    def calculate_live_runtime(login_time_str: str) -> str:
        try:
            if "T" in login_time_str:  # ISO format from hybrid
                start = datetime.fromisoformat(login_time_str.replace('Z', '+00:00'))
            else:  # Legacy format
                start = datetime.strptime(login_time_str, "%Y-%m-%d %H:%M:%S")
            delta = datetime.now() - start
            return format_runtime_from_delta(delta)
        except Exception:
            return "-"

    def refresh_table():
        users = load_users()
        table.rows.clear()
        runtime_labels.clear()

        # Get active sessions using existing session system
        active_sessions = get_active_sessions()

        page_width = content.page.width if content.page else 1200
        refresh_columns_for_width(page_width)

        query = search_field.value.lower().strip()
        selected_filter = filter_mode["value"]
        users_list = list(users.items())

        if selected_filter == "Sort by Name (A–Z)":
            users_list.sort(key=lambda x: x[1].get("fullname", "").lower())
        elif selected_filter == "Sort by Email (A–Z)":
            users_list.sort(key=lambda x: x[0].lower())
        elif selected_filter == "Sort by Username (A–Z)":
            users_list.sort(key=lambda x: x[1].get("username", "").lower())
        elif selected_filter == "Filter by Role (ADMIN)":
            users_list = [u for u in users_list if u[1].get("role", "").upper() == "ADMIN"]
        elif selected_filter == "Filter by Role (USER)":
            users_list = [u for u in users_list if u[1].get("role", "").upper() == "USER"]
        elif selected_filter == "Filter by Role (TEAM_LEADER)":
            users_list = [u for u in users_list if u[1].get("role", "").upper() == "TEAM_LEADER"]
        elif selected_filter == "Filter by Team":
            users_list = [u for u in users_list if "KUSAKABE" in u[1].get("team_tags", [])]

        team_options = refresh_team_options()

        for email, data in users_list:
            uname = data.get("username", "")
            role = (data.get("role", "") or "").upper()

            if query and query not in data.get("fullname", "").lower() and query not in email.lower():
                continue

            runtime_text = "-"
            session_key = f"{uname}:{role}"

            if session_key in active_sessions:
                login_time = active_sessions[session_key]["login_time"]
                runtime_text = calculate_live_runtime(login_time)
            else:
                runtime_text = get_last_runtime(uname)

            cells = []
            for col_name, always in all_columns:
                if col_name == "Password" and page_width < 1000:
                    continue
                if col_name == "Team" and page_width < 1000:
                    continue

                if col_name == "Full Name":
                    cells.append(ft.DataCell(ft.Text(data.get("fullname", ""), weight=FontWeight.BOLD)))
                elif col_name == "Email":
                    cells.append(ft.DataCell(ft.Text(email)))
                elif col_name == "Username":
                    cells.append(ft.DataCell(ft.Text(uname)))
                elif col_name == "Password":
                    cells.append(ft.DataCell(ft.Text("••••••")))
                elif col_name == "Role":
                    if edit_mode["value"]:
                        role_dropdown = ft.Dropdown(
                            options=[
                                ft.dropdown.Option("ADMIN"), 
                                ft.dropdown.Option("USER"),
                                ft.dropdown.Option("TEAM_LEADER")
                            ],
                            value=role,
                            on_change=lambda e, u=email: update_role(u, e.control.value)
                        )
                        cells.append(ft.DataCell(role_dropdown))
                    else:
                        # Enhanced role badge with color coding
                        if role == "ADMIN":
                            role_color = ft.Colors.RED
                        elif role == "TEAM_LEADER":
                            role_color = ft.Colors.BLUE
                        else:
                            role_color = ft.Colors.GREEN
                            
                        role_badge = ft.Container(
                            content=ft.Text(role, color="white", size=11, weight=ft.FontWeight.BOLD),
                            bgcolor=role_color,
                            padding=ft.padding.symmetric(horizontal=8, vertical=4),
                            border_radius=8
                        )
                        cells.append(ft.DataCell(role_badge))
                elif col_name == "Team":
                    tags_list = data.get("team_tags", [])
                    if edit_mode["value"]:
                        tags_dropdown = ft.Dropdown(
                            options=team_options,
                            value=tags_list[0] if tags_list else None,
                            on_change=lambda e, u=email: update_team_tags(u, [e.control.value])
                        )
                        cells.append(ft.DataCell(tags_dropdown))
                    else:
                        cells.append(ft.DataCell(ft.Text(", ".join(tags_list) if tags_list else "")))
                elif col_name == "Runtime":
                    runtime_lbl = ft.Text(runtime_text)
                    runtime_labels[email] = (runtime_lbl, session_key)
                    cells.append(ft.DataCell(runtime_lbl))
                elif col_name == "Remove User":
                    def confirm_delete(e, u=email):
                        show_center_sheet(
                            content.page,
                            title="Confirm Delete",
                            message=f"Are you sure you want to delete user '{u}'?",
                            on_confirm=lambda: delete_user(u)
                        )

                    delete_btn = ft.ElevatedButton(
                        "Delete",
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                    ft.ControlState.HOVERED: ft.Colors.RED_100},
                            color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                ft.ControlState.HOVERED: ft.Colors.RED},
                            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.with_opacity(0.0, ft.Colors.BLACK))},
                            shape=ft.RoundedRectangleBorder(radius=2)
                        ),
                        on_click=confirm_delete,
                        icon=ft.Icons.DELETE_OUTLINED,
                    )
                    cells.append(ft.DataCell(delete_btn))

            table.rows.append(ft.DataRow(cells=cells))

        content.update()

    def update_role(user_email, new_role):
        """Update user role in hybrid or legacy system"""
        if hybrid_app:
            try:
                # Update in hybrid backend
                user_data = {'role': new_role}
                hybrid_app.user_service.update_user(user_email, user_data)
                print(f"✅ Hybrid: Updated role for {user_email}")
            except Exception as e:
                print(f"⚠️ Error updating role in hybrid: {e}")
                # Fallback to legacy
                update_role_legacy(user_email, new_role)
        else:
            update_role_legacy(user_email, new_role)
        
        # Log activity using existing logger
        log_activity(username, f"Changed role of {user_email} to {new_role}")
        refresh_table()

    def update_role_legacy(user_email, new_role):
        """Legacy role update"""
        users = load_users()
        if user_email in users:
            old_role = users[user_email].get("role")
            users[user_email]["role"] = new_role
            save_users(users)

    def update_team_tags(user_email, new_tags):
        """Update user team tags in hybrid or legacy system"""
        if hybrid_app:
            try:
                # Update in hybrid backend
                user_data = {'team_tags': new_tags}
                hybrid_app.user_service.update_user(user_email, user_data)
                print(f"✅ Hybrid: Updated teams for {user_email}")
            except Exception as e:
                print(f"⚠️ Error updating teams in hybrid: {e}")
                # Fallback to legacy
                update_team_tags_legacy(user_email, new_tags)
        else:
            update_team_tags_legacy(user_email, new_tags)
        
        # Log activity using existing logger
        log_activity(username, f"Changed team of {user_email} to {new_tags}")
        refresh_table()

    def update_team_tags_legacy(user_email, new_tags):
        """Legacy team tags update"""
        users = load_users()
        if user_email in users:
            old_team = users[user_email].get("team_tags", [])
            users[user_email]["team_tags"] = new_tags
            save_users(users)

    def delete_user(user_email):
        """Delete user from hybrid or legacy system"""
        if hybrid_app:
            try:
                # Delete from hybrid backend
                hybrid_app.user_service.delete_user(user_email)
                print(f"✅ Hybrid: Deleted user {user_email}")
            except Exception as e:
                print(f"⚠️ Error deleting user from hybrid: {e}")
                # Fallback to legacy
                delete_user_legacy(user_email)
        else:
            delete_user_legacy(user_email)
        
        # Log activity using existing logger
        log_activity(username, f"Deleted user {user_email}")
        refresh_table()

    def delete_user_legacy(user_email):
        """Legacy user deletion"""
        users = load_users()
        if user_email in users:
            users.pop(user_email)
            save_users(users)

    def toggle_edit_mode(e):
        edit_mode["value"] = not edit_mode["value"]
        refresh_table()

    def go_to_add_user(e):
        """Use existing add_user.py"""
        from admin.add_user import add_user_hybrid_page
        add_user_hybrid_page(content, content.page, username, hybrid_app)

    def go_to_reset_password(e):
        """Use existing reset_password.py"""
        from admin.reset_password import reset_password_hybrid_page
        reset_password_hybrid_page(content, content.page, username, hybrid_app)

    buttons_row = ft.Row(
        controls=[
            ft.ElevatedButton("Assign Roles",
                              on_click=toggle_edit_mode,
                              icon=ft.Icons.EDIT,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                           ft.ControlState.HOVERED: ft.Colors.GREY_200},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.BLACK},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            ft.ElevatedButton("Add User",
                              icon=ft.Icons.ADD,
                              on_click=go_to_add_user,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                           ft.ControlState.HOVERED: ft.Colors.GREY_200},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.BLACK},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            ft.ElevatedButton("Reset Password",
                              icon=ft.Icons.LOCK_RESET,
                              on_click=go_to_reset_password,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                           ft.ControlState.HOVERED: ft.Colors.GREY_200},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.BLACK},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              )
        ],
        alignment=ft.MainAxisAlignment.END,
    )

    top_controls = ft.Row(
        controls=[
            search_field,
            filter_dropdown,
            ft.Container(expand=True),
            buttons_row
        ],
        expand=True,
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    table_container = ft.Container(
        ft.Row([table], expand=True),
        expand=True
    )

    main_container = ft.Container(
        content=ft.Column([
            system_status,
            top_controls, 
            ft.Divider(), 
            table_container
        ], expand=True),
        margin=ft.margin.only(left=50, right=50, top=20),
        expand=True,
    )

    content.controls.append(main_container)
    refresh_table()

    def on_resized(e):
        refresh_table()

    content.page.on_resized = on_resized

    async def periodic_refresh():
        while True:
            await asyncio.sleep(1)
            
            # Get active sessions using existing session system
            active_sessions = get_active_sessions()
            
            # Update runtime labels
            for email, (lbl, session_key) in runtime_labels.items():
                if session_key in active_sessions:
                    login_time = active_sessions[session_key]["login_time"]
                    lbl.value = calculate_live_runtime(login_time)
            
            content.update()

    content.page.run_task(periodic_refresh)