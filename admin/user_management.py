import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
import hashlib
import asyncio
from datetime import datetime, timedelta
from admin.utils.team_utils import get_team_options
from utils.session_logger import log_activity
import json
from utils.dialog import show_center_sheet

# Dashboard styling constants - same as activity_logs.py
PANEL_COLOR = "#FFFFFF"
PANEL_RADIUS = 14



def user_management(content: ft.Column, username: Optional[str]):
    content.controls.clear()

    users_file = r"\\KMTI-NAS\Shared\data\users.json"
    edit_mode = {"value": False}
    filter_mode = {"value": "All"}

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
        if not os.path.exists(users_file):
            return {}
        with open(users_file, "r") as f:
            users = json.load(f)
        if migrate_plain_passwords(users):
            save_users(users)
        return users

    def save_users(data):
        with open(users_file, "w") as f:
            json.dump(data, f, indent=4)

    users = load_users()

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
        ("Remove User", True),
    ]

    table = ft.DataTable(
        expand=True,
        columns=[],
        rows=[],
        width=None,  # Allow flexible width
        column_spacing=10,
        horizontal_margin=5,
        data_row_max_height=60,
        data_row_min_height=40,
        divider_thickness=1,
    )

    def refresh_columns_for_width(width: int):
        table.columns.clear()

        # More aggressive column hiding for smaller screens
        show_password = width >= 900  # Lower threshold
        show_team = width >= 800      # Lower threshold
        show_username = width >= 700   # Hide username on very small screens
        show_full_name = width >= 500  # Show only if there's enough space

        for col_name, always in all_columns:
            if col_name == "Password" and not show_password:
                continue
            if col_name == "Team" and not show_team:
                continue
            if col_name == "Username" and not show_username:
                continue
            if col_name == "Full Name" and not show_full_name:
                continue
            
            # Add responsive column with appropriate sizing
            column_text = ft.Text(col_name, weight=ft.FontWeight.BOLD, size=14)
            table.columns.append(ft.DataColumn(column_text))

        # Adjust row size and spacing based on width
        if width > 1200:
            table.heading_row_height = 60
            table.data_row_min_height = 60
            table.column_spacing = 15
            table.horizontal_margin = 10
        elif width > 800:
            table.heading_row_height = 50
            table.data_row_min_height = 50
            table.column_spacing = 12
            table.horizontal_margin = 8
        elif width > 600:
            table.heading_row_height = 45
            table.data_row_min_height = 45
            table.column_spacing = 8
            table.horizontal_margin = 5
        else:
            table.heading_row_height = 40
            table.data_row_min_height = 40
            table.column_spacing = 5
            table.horizontal_margin = 2

    def refresh_team_options():
        return [ft.dropdown.Option(opt) for opt in get_team_options()]

    def apply_filter(value: str):
        filter_mode["value"] = value
        refresh_table()




    

    

    


    def refresh_table():
        users = load_users()
        table.rows.clear()

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
        elif selected_filter == "Filter by Role (TEAM LEADER)":
            users_list = [u for u in users_list if u[1].get("role", "").upper() == "TEAM LEADER"]
        elif selected_filter == "Filter by Role (USER)":
            users_list = [u for u in users_list if u[1].get("role", "").upper() == "USER"]
        elif selected_filter == "Filter by Team":
            users_list = [u for u in users_list if "KUSAKABE" in u[1].get("team_tags", [])]

        team_options = refresh_team_options()

        for email, data in users_list:
            uname = data.get("username", "")
            role = (data.get("role", "") or "").upper()

            if query and query not in data.get("fullname", "").lower() and query not in email.lower():
                continue

            cells = []
            
            # Determine what columns to show based on screen width
            show_password = page_width >= 900
            show_team = page_width >= 800
            show_username = page_width >= 700
            show_full_name = page_width >= 500
            
            for col_name, always in all_columns:
                if col_name == "Password" and not show_password:
                    continue
                if col_name == "Team" and not show_team:
                    continue
                if col_name == "Username" and not show_username:
                    continue
                if col_name == "Full Name" and not show_full_name:
                    continue

                if col_name == "Full Name":
                    cells.append(ft.DataCell(ft.Text(data.get("fullname", ""), weight=FontWeight.BOLD, size=13)))
                elif col_name == "Email":
                    cells.append(ft.DataCell(ft.Text(email, size=13)))
                elif col_name == "Username":
                    cells.append(ft.DataCell(ft.Text(uname, size=13)))
                elif col_name == "Password":
                    cells.append(ft.DataCell(ft.Text("••••••", size=13)))
                elif col_name == "Role":
                    if edit_mode["value"]:
                        role_dropdown = ft.Dropdown(
                            options=[ft.dropdown.Option("ADMIN"), 
                                     ft.dropdown.Option("USER"),
                                     ft.dropdown.Option("TEAM LEADER")],
                            value=role,
                            on_change=lambda e, u=email: update_role(u, e.control.value),
                            width=120 if page_width < 800 else 150
                        )
                        cells.append(ft.DataCell(role_dropdown))
                    else:
                        cells.append(ft.DataCell(ft.Text(role, size=13)))
                elif col_name == "Team":
                    tags_list = data.get("team_tags", [])
                    if edit_mode["value"]:
                        tags_dropdown = ft.Dropdown(
                            options=team_options,
                            value=tags_list[0] if tags_list else None,
                            on_change=lambda e, u=email: update_team_tags(u, [e.control.value]),
                            width=120 if page_width < 800 else 150
                        )
                        cells.append(ft.DataCell(tags_dropdown))
                    else:
                        team_text = ", ".join(tags_list) if tags_list else ""
                        # Truncate team text for smaller screens
                        if page_width < 900 and len(team_text) > 15:
                            team_text = team_text[:12] + "..."
                        cells.append(ft.DataCell(ft.Text(team_text, size=13)))
                elif col_name == "Remove User":
                    def confirm_delete(e, u=email):
                        show_center_sheet(
                            content.page,
                            title="Confirm Delete",
                            message=f"Are you sure you want to delete user '{u}'?",
                            on_confirm=lambda: delete_user(u)
                        )

                    # Smaller button for mobile screens
                    button_text = "Del" if page_width < 600 else "Delete"
                    delete_btn = ft.ElevatedButton(
                        button_text,
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                    ft.ControlState.HOVERED: ft.Colors.RED},
                            color={ft.ControlState.DEFAULT: ft.Colors.RED,
                                ft.ControlState.HOVERED: ft.Colors.WHITE},
                            side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED)},
                            shape=ft.RoundedRectangleBorder(radius=6)
                        ),
                        on_click=confirm_delete,
                        icon=ft.Icons.DELETE_OUTLINED,
                        width=60 if page_width < 600 else None
                    )
                    cells.append(ft.DataCell(delete_btn))

            table.rows.append(ft.DataRow(cells=cells))

        # Update container width responsively after table refresh
        update_responsive_layout()
        
        # Ensure table width is properly set for centering
        table.width = None  # Allow table to be flexible
        table.expand = True
        
        content.update()

    def update_role(user_email, new_role):
        users = load_users()
        if user_email in users:
            old_role = users[user_email].get("role")
            users[user_email]["role"] = new_role
            save_users(users)

            # Log activity
            log_activity(username, f"Changed role of {user_email} from {old_role} to {new_role}")
            refresh_table()

    def update_team_tags(user_email, new_tags):
        users = load_users()
        if user_email in users:
            old_team = users[user_email].get("team_tags", [])
            users[user_email]["team_tags"] = new_tags
            save_users(users)

            # Log activity
            log_activity(username, f"Changed team of {user_email} from {old_team} to {new_tags}")
            refresh_table()

    def delete_user(user_email):
        users = load_users()
        if user_email in users:
            users.pop(user_email)
            save_users(users)

            # Log activity
            log_activity(username, f"Deleted user {user_email}")
        refresh_table()

    def toggle_edit_mode(e):
        edit_mode["value"] = not edit_mode["value"]
        refresh_table()

    def go_to_add_user(e):
        from admin.components.add_user import add_user_page
        add_user_page(content, content.page, username)

    def go_to_reset_password(e):
        from admin.components.reset_password import reset_password_page
        reset_password_page(content, content.page, username)

    def update_responsive_layout():
        """Update layout based on screen size with proper centering for all sizes"""
        page_width = content.page.width if content.page else 1200
        
        # Calculate responsive margins and widths with better small screen support
        if page_width < 600:  # Extra small screens
            margin_horizontal = 5
            max_width = page_width - 10
            search_field.width = min(200, page_width - 50)
            filter_dropdown.width = min(120, page_width - 250)
        elif page_width < 768:  # Small screens
            margin_horizontal = 8
            max_width = page_width - 16
            search_field.width = min(250, page_width - 80)
            filter_dropdown.width = 140
        elif page_width < 1024:  # Tablet
            margin_horizontal = 15
            max_width = page_width - 30
            search_field.width = min(300, page_width - 200)
            filter_dropdown.width = 160
        elif page_width < 1440:  # Desktop
            margin_horizontal = 20
            max_width = min(1200, page_width - 40)
            search_field.width = 350
            filter_dropdown.width = 180
        else:  # Large screens - use percentage-based width for better centering
            margin_horizontal = 30
            max_width = min(1400, int(page_width * 0.6))  # 90% of screen width
            search_field.width = 400
            filter_dropdown.width = 180
        
        # Update main container with responsive settings
        main_container.margin = ft.margin.only(
            left=margin_horizontal, 
            right=margin_horizontal, 
            top=20
        )
        main_container.width = max_width
        main_container.alignment = ft.alignment.center
        
        # Update table container to consume full available width
        table_container.width = None  # Let it consume container width
        table_container.expand = True
        
        # Update table properties for better responsiveness - make it consume parent width
        table.width = None  # Let table consume full container width
        table.expand = True
        
        # Recreate top controls with new layout
        new_top_controls = create_top_controls()
        main_container.content.controls[0] = new_top_controls
        
        try:
            main_container.update()
            table_container.update()
            search_field.update()
            filter_dropdown.update()
            table.update()
        except:
            pass

    buttons_row = ft.Row(
        controls=[
            ft.ElevatedButton("Assign Roles",
                              on_click=toggle_edit_mode,
                              icon=ft.Icons.EDIT,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                           ft.ControlState.HOVERED: ft.Colors.BLACK},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            ft.ElevatedButton("Add User",
                              icon=ft.Icons.ADD,
                              on_click=go_to_add_user,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                           ft.ControlState.HOVERED: ft.Colors.GREEN},
                                  color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            ft.ElevatedButton("Reset Password",
                              icon=ft.Icons.LOCK_RESET,
                              on_click=go_to_reset_password,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                           ft.ControlState.HOVERED: ft.Colors.RED},
                                  color={ft.ControlState.DEFAULT: ft.Colors.RED,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              )
        ],
        alignment=ft.MainAxisAlignment.END,
    )

    # Create responsive top controls
    def create_top_controls():
        page_width = content.page.width if content.page else 1200
        
        # Responsive layout based on screen size
        if page_width < 600:  # Extra small - stack everything
            return ft.Column([
                ft.Container(height=10),
                ft.Column([
                    search_field,
                    ft.Container(height=8),
                    filter_dropdown,
                ], spacing=0),
                ft.Container(height=10),
                ft.Column([
                    ft.Row([
                        ft.ElevatedButton("Assign",
                                          on_click=toggle_edit_mode,
                                          icon=ft.Icons.EDIT,
                                          style=ft.ButtonStyle(
                                              bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                                       ft.ControlState.HOVERED: ft.Colors.BLACK},
                                              color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                                     ft.ControlState.HOVERED: ft.Colors.WHITE},
                                              side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.BLACK)},
                                              shape=ft.RoundedRectangleBorder(radius=5))
                                          ),
                        ft.ElevatedButton("Add",
                                          icon=ft.Icons.ADD,
                                          on_click=go_to_add_user,
                                          style=ft.ButtonStyle(
                                              bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                                       ft.ControlState.HOVERED: ft.Colors.GREEN},
                                              color={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                                                     ft.ControlState.HOVERED: ft.Colors.WHITE},
                                              side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.GREEN)},
                                              shape=ft.RoundedRectangleBorder(radius=5))
                                          ),
                        ft.ElevatedButton("Reset",
                                          icon=ft.Icons.LOCK_RESET,
                                          on_click=go_to_reset_password,
                                          style=ft.ButtonStyle(
                                              bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_100,
                                                       ft.ControlState.HOVERED: ft.Colors.RED},
                                              color={ft.ControlState.DEFAULT: ft.Colors.RED,
                                                     ft.ControlState.HOVERED: ft.Colors.WHITE},
                                              side={ft.ControlState.DEFAULT: ft.BorderSide(1, ft.Colors.RED)},
                                              shape=ft.RoundedRectangleBorder(radius=5))
                                          )
                    ], alignment=ft.MainAxisAlignment.SPACE_EVENLY, tight=True)
                ], spacing=5),
            ], spacing=5)
        elif page_width < 768:  # Small screens - stack vertically
            return ft.Column([
                ft.Container(height=12),
                ft.Row([
                    search_field,
                    ft.Container(width=10),
                    filter_dropdown,
                ], alignment=ft.MainAxisAlignment.START),
                ft.Container(height=10),
                ft.Row([
                    buttons_row
                ], alignment=ft.MainAxisAlignment.END),
            ], spacing=5)
        else:  # Desktop/Tablet - horizontal layout
            return ft.Column([
                ft.Container(height=15),
                ft.Row(
                    controls=[
                        search_field,
                        filter_dropdown,
                        ft.Container(expand=True),
                        buttons_row
                    ],
                    expand=True,
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
            ])

    top_controls = create_top_controls()

    table_container = ft.Container(
        content=ft.Column([
            ft.Container(
                content=table,
                expand=True,
                width=None,  # Allow table to consume full width
                height=None,  # Allow table to consume full height
                alignment=ft.alignment.center
            )
        ], 
        expand=True,
        spacing=0,
        horizontal_alignment=ft.CrossAxisAlignment.STRETCH,  # Stretch to fill width
        scroll=ft.ScrollMode.AUTO),
        bgcolor=PANEL_COLOR,
        border_radius=PANEL_RADIUS,
        padding=20,
        shadow=ft.BoxShadow(
            blur_radius=8,
            spread_radius=1,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
        ),
        expand=True,
        width=None,  # Allow container to be fully responsive
        height=None,  # Allow container to expand
        alignment=ft.alignment.center
    )

    main_container = ft.Container(
        content=ft.Column([
            top_controls, 
            ft.Container(height=20),  # Add spacing like in activity_logs.py
            table_container
        ], expand=True),
        margin=ft.margin.only(left=20, right=20, top=20),  # Reduced margins for smaller screens
        expand=True,  # Allow expansion for responsiveness
        alignment=ft.alignment.center,
        width=None,  # Allow responsive width calculation
    )

    # Wrapper container to center the main content for all screen sizes
    centered_wrapper = ft.Container(
        content=main_container,
        expand=True,
        alignment=ft.alignment.center,
        width=None,
        height=None
    )

    content.controls.append(centered_wrapper)
    refresh_table()

    def on_resized(e):
        refresh_table()

    content.page.on_resized = on_resized