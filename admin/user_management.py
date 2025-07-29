import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
import hashlib
import datetime
import asyncio
from admin.utils.team_utils import get_team_options


def user_management(content: ft.Column, username: Optional[str]):
    content.controls.clear()

    users_file = "data/users.json"
    edit_mode = {"value": False}
    filter_mode = {"value": "All"}
    runtime_labels = {}  # Store references to runtime Text widgets

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
        width=400,
        border_radius=10,
        on_change=lambda e: refresh_table()
    )

    filter_dropdown = ft.Dropdown(
        label="Filter / Sort",
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

    table = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Full Name")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Username")),
            ft.DataColumn(ft.Text("Password")),
            ft.DataColumn(ft.Text("Role")),
            ft.DataColumn(ft.Text("Team")),
            ft.DataColumn(ft.Text("Runtime")),
            ft.DataColumn(ft.Text("Remove User")),
        ],
        rows=[]
    )

    def refresh_team_options():
        return [ft.dropdown.Option(opt) for opt in get_team_options()]

    def apply_filter(value: str):
        filter_mode["value"] = value
        refresh_table()

    def calculate_runtime(runtime_start: str) -> str:
        try:
            start_time = datetime.datetime.fromisoformat(runtime_start)
        except Exception:
            return "N/A"
        delta = datetime.datetime.now() - start_time
        hours, remainder = divmod(delta.seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{delta.days}d {hours}h {minutes}m {seconds}s"

    def refresh_table():
        users = load_users()
        table.rows.clear()
        runtime_labels.clear()

        query = search_field.value.lower().strip()
        selected_filter = filter_mode["value"]
        users_list = list(users.items())

        # Sorting / filtering
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
            if query and query not in data.get("fullname", "").lower() and query not in email.lower():
                continue

            fullname_text = ft.Text(data.get("fullname", ""), weight=FontWeight.BOLD)
            email_text = ft.Text(email)
            username_text = ft.Text(data.get("username", ""))
            password_text = ft.Text("••••••")

            # Runtime only for currently logged-in user
            if username == data.get("username"):
                runtime_text = ft.Text(calculate_runtime(data.get("runtime_start", datetime.datetime.now().isoformat())))
                runtime_labels[email] = runtime_text
            else:
                runtime_text = ft.Text("-")

            # Role column
            if edit_mode["value"]:
                role_dropdown = ft.Dropdown(
                    options=[ft.dropdown.Option("ADMIN"), ft.dropdown.Option("USER")],
                    value=data.get("role", "user"),
                    on_change=lambda e, u=email: update_role(u, e.control.value)
                )
                role_widget = role_dropdown
            else:
                role_widget = ft.Text(data.get("role", ""))

            # Team column
            tags_list = data.get("team_tags", [])
            if edit_mode["value"]:
                tags_dropdown = ft.Dropdown(
                    options=team_options,
                    value=tags_list[0] if tags_list else None,
                    on_change=lambda e, u=email: update_team_tags(u, [e.control.value])
                )
                team_tags_widget = tags_dropdown
            else:
                team_tags_widget = ft.Text(", ".join(tags_list) if tags_list else "")

            # Delete button
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
                on_click=lambda e, u=email: delete_user(u)
            )

            table.rows.append(
                ft.DataRow(
                    cells=[
                        ft.DataCell(ft.Container(fullname_text, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Container(email_text, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Container(username_text, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Container(password_text, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Container(role_widget, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Container(team_tags_widget, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Container(runtime_text, alignment=ft.alignment.center)),
                        ft.DataCell(ft.Container(delete_btn, alignment=ft.alignment.center)),
                    ]
                )
            )

        content.update()

    def update_role(user_email, new_role):
        users = load_users()
        if user_email in users:
            users[user_email]["role"] = new_role
            save_users(users)
            refresh_table()

    def update_team_tags(user_email, new_tags):
        users = load_users()
        if user_email in users:
            users[user_email]["team_tags"] = new_tags
            save_users(users)
            refresh_table()

    def delete_user(user_email):
        users = load_users()
        if user_email in users:
            users.pop(user_email)
            save_users(users)
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

    # Buttons row
    buttons_row = ft.Row(
        controls=[
            ft.ElevatedButton(
                "Assign Roles",
                on_click=toggle_edit_mode,
                icon=ft.Icons.EDIT,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                             ft.ControlState.HOVERED: ft.Colors.BLACK},
                    side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK)},
                    color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                    shape=ft.RoundedRectangleBorder(radius=5),
                )),
            ft.ElevatedButton(
                "Add User",
                icon=ft.Icons.ADD,
                on_click=go_to_add_user,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                             ft.ControlState.HOVERED: ft.Colors.GREEN},
                    shape=ft.RoundedRectangleBorder(radius=5),
                    color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                )),
            ft.ElevatedButton(
                "Reset Password",
                on_click=go_to_reset_password,
                icon=ft.Icons.LOCK_RESET,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                             ft.ControlState.HOVERED: ft.Colors.RED},
                    shape=ft.RoundedRectangleBorder(radius=5),
                    color={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                )),
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
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    main_container = ft.Container(
        content=ft.Column([top_controls, ft.Divider(), table]),
        margin=ft.margin.only(left=50, right=50, top=20),
        expand=True,
    )

    content.controls.append(main_container)
    refresh_table()

    # Auto-refresh runtime for currently logged-in user
    async def periodic_refresh():
        while True:
            await asyncio.sleep(1)
            users = load_users()
            for email, lbl in runtime_labels.items():
                start = users.get(email, {}).get("runtime_start")
                if start:
                    lbl.value = calculate_runtime(start)
            content.update()

    content.page.run_task(periodic_refresh)
