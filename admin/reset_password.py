import flet as ft
import json
import os
import hashlib
from utils.session_logger import log_activity

USERS_FILE = "data/users.json"


def reset_password_page(content, page, admin_username):
    """Reset password UI with logging of reset actions."""

    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()

    def load_users():
        if not os.path.exists(USERS_FILE):
            return {}
        with open(USERS_FILE, "r") as f:
            return json.load(f)

    def save_users(users):
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)

    users = load_users()

    # Dropdown for selecting an existing user
    email_dropdown = ft.Dropdown(
        label="Select user to reset",
        width=400,
        options=[ft.dropdown.Option(email) for email in users.keys()],
    )

    new_password = ft.TextField(
        label="New Password",
        password=True,
        can_reveal_password=True,
        width=400
    )

    def save_new_password(e):
        users = load_users()
        selected_email = email_dropdown.value
        if selected_email in users:
            users[selected_email]["password"] = hash_password(new_password.value)
            save_users(users)

            # Log the password reset action
            log_activity(admin_username, f"Reset password for user {selected_email}")

            # After saving, return to the user management page (same as Add User)
            from admin.user_management import user_management
            content.controls.clear()
            user_management(content, admin_username)

        else:
            page.snack_bar = ft.SnackBar(content=ft.Text("User not found!"))
            page.snack_bar.open = True
            page.update()

    def go_back(e):
        from admin.user_management import user_management
        content.controls.clear()
        user_management(content, admin_username)

    # Layout
    form = ft.Column(
        [
            ft.Text("Reset User Password", size=24, weight="bold"),
            email_dropdown,
            new_password,
            ft.Row(
                [
                    ft.ElevatedButton(
                        "Save",
                        on_click=save_new_password,
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                     ft.ControlState.HOVERED: ft.Colors.GREEN},
                            color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                   ft.ControlState.HOVERED: ft.Colors.WHITE},
                            side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.GREEN)},
                            shape=ft.RoundedRectangleBorder(radius=5)
                        )
                    ),
                    ft.ElevatedButton(
                        "Back",
                        on_click=go_back,
                        style=ft.ButtonStyle(
                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                     ft.ControlState.HOVERED: ft.Colors.RED},
                            color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                   ft.ControlState.HOVERED: ft.Colors.WHITE},
                            side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.RED)},
                            shape=ft.RoundedRectangleBorder(radius=5)
                        )
                    ),
                ],
                alignment=ft.MainAxisAlignment.CENTER,
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.START,
        spacing=15,
    )

    # Clear and display
    content.controls.clear()
    content.controls.append(
        ft.Row(
            controls=[
                ft.Container(
                    content=form,
                    padding=20,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True,
        )
    )
    page.update()
