import flet as ft
from flet import FontWeight
from typing import Optional
import json
import os
import hashlib
from admin.utils.team_utils import get_team_options


def user_management(content: ft.Column, username: Optional[str]):
    content.controls.clear()

    users_file = "data/users.json"
    edit_mode = {"value": False}

    def hash_password(password: str) -> str:
        """Convert password to a SHA-256 hash."""
        return hashlib.sha256(password.encode()).hexdigest()

    def migrate_plain_passwords(users):
        """Convert any plain text password to hashed."""
        changed = False
        for email, data in users.items():
            pw = data.get("password", "")
            # Detect if it's plain text (not 64 hex chars)
            if len(pw) != 64 or not all(c in "0123456789abcdef" for c in pw.lower()):
                data["password"] = hash_password(pw)
                changed = True
        return changed

    def load_users():
        if not os.path.exists(users_file):
            return {}
        with open(users_file, "r") as f:
            users = json.load(f)
        # Auto migrate plain text passwords
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

    table = ft.DataTable(
        expand=True,
        columns=[
            ft.DataColumn(ft.Text("Full Name")),
            ft.DataColumn(ft.Text("Email")),
            ft.DataColumn(ft.Text("Username")),
            ft.DataColumn(ft.Text("Password")),
            ft.DataColumn(ft.Text("Role")),
            ft.DataColumn(ft.Text("Team")),
            ft.DataColumn(ft.Text("Remove User")),
        ],
        rows=[]
    )

    def refresh_team_options():
        return [ft.dropdown.Option(opt) for opt in get_team_options()]

    def refresh_table():
        users = load_users()
        table.rows.clear()
        query = search_field.value.lower().strip()
        team_options = refresh_team_options()

        for email, data in users.items():
            if query and query not in data.get("fullname", "").lower() and query not in email.lower():
                continue

            fullname_text = ft.Text(data.get("fullname", ""), weight=FontWeight.BOLD)
            email_text = ft.Text(email)
            username_text = ft.Text(data.get("username", ""))
            password_text = ft.Text("••••••")  # Always masked

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
                # Display as plain text
                team_tags_widget = ft.Text(", ".join(tags_list) if tags_list else "")

            # Delete button - instant delete
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
                        ft.DataCell(fullname_text),
                        ft.DataCell(email_text),
                        ft.DataCell(username_text),
                        ft.DataCell(password_text),
                        ft.DataCell(role_widget),
                        ft.DataCell(team_tags_widget),
                        ft.DataCell(delete_btn),
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

    def reset_password_dialog(e):
        new_pass = ft.TextField(label="Enter new password", password=True)

        def submit_password(ev):
            selected_email = None
            users = load_users()
            if len(users) == 1:
                selected_email = list(users.keys())[0]
            if selected_email:
                # Hash the new password before saving
                users[selected_email]["password"] = hash_password(new_pass.value)
                save_users(users)
            refresh_table()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Reset Password"),
            content=new_pass,
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: close_dialog()),
                ft.TextButton("Submit", on_click=submit_password),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        content.page.dialog = dlg
        dlg.open = True
        content.page.update()

    def close_dialog():
        content.page.dialog.open = False
        content.page.update()

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
                on_click=reset_password_dialog,
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

    # Top controls layout
    top_controls = ft.Row(
        controls=[
            search_field,
            ft.Container(expand=True),
            buttons_row
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
    )

    main_container = ft.Container(
        content=ft.Column([top_controls, ft.Divider(), table]),
        margin=ft.margin.only(left=100, right=50, top=20),
        expand=True,
    )

    content.controls.append(main_container)
    refresh_table()
