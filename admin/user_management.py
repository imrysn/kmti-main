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


def user_management(content: ft.Column, username: Optional[str]):
    content.controls.clear()

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
        return [ft.dropdown.Option(opt) for opt in get_team_options()]

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
            start = datetime.strptime(login_time_str, "%Y-%m-%d %H:%M:%S")
            delta = datetime.now() - start
            return format_runtime_from_delta(delta)
        except Exception:
            return "-"

    def refresh_table():
        users = load_users()
        table.rows.clear()
        runtime_labels.clear()

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
                            options=[ft.dropdown.Option("ADMIN"), ft.dropdown.Option("USER")],
                            value=role,
                            on_change=lambda e, u=email: update_role(u, e.control.value)
                        )
                        cells.append(ft.DataCell(role_dropdown))
                    else:
                        cells.append(ft.DataCell(ft.Text(role)))
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
                    delete_btn = ft.ElevatedButton(
                        "Delete",
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.RED,
                                     ft.ControlState.HOVERED: ft.Colors.WHITE},
                            color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                   ft.ControlState.HOVERED: ft.Colors.RED},
                            side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
                            shape=ft.RoundedRectangleBorder(radius=5),
                        ),
                        on_click=lambda e, u=email: delete_user(u),
                        icon=ft.Icons.DELETE,
                    )
                    cells.append(ft.DataCell(delete_btn))

            table.rows.append(ft.DataRow(cells=cells))

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
        from admin.add_user import add_user_page
        add_user_page(content, content.page, username)

    def go_to_reset_password(e):
        from admin.reset_password import reset_password_page
        reset_password_page(content, content.page, username)

    buttons_row = ft.Row(
        controls=[
            ft.ElevatedButton("Assign Roles",
                              on_click=toggle_edit_mode,
                              icon=ft.Icons.EDIT,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.BLACK},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            ft.ElevatedButton("Add User",
                              icon=ft.Icons.ADD,
                              on_click=go_to_add_user,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.GREEN},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                                  shape=ft.RoundedRectangleBorder(radius=5))
                              ),
            ft.ElevatedButton("Reset Password",
                              icon=ft.Icons.LOCK_RESET,
                              on_click=go_to_reset_password,
                              style=ft.ButtonStyle(
                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                           ft.ControlState.HOVERED: ft.Colors.RED},
                                  color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                         ft.ControlState.HOVERED: ft.Colors.WHITE},
                                  side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
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
        content=ft.Column([top_controls, ft.Divider(), table_container], expand=True),
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
            active_sessions = get_active_sessions()
            for email, (lbl, session_key) in runtime_labels.items():
                if session_key in active_sessions:
                    login_time = active_sessions[session_key]["login_time"]
                    lbl.value = calculate_live_runtime(login_time)
            content.update()

    content.page.run_task(periodic_refresh)
