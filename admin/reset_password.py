import flet as ft
import json
import os
import hashlib
from typing import Optional

USERS_FILE = "data/users.json"


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


def reset_password_page(content: ft.Column, page: ft.Page, username: Optional[str]):
    content.controls.clear()

    users = load_users()
    email_dropdown = ft.Dropdown(
        label="Select User",
        options=[ft.dropdown.Option(email) for email in users.keys()],
        width=400,
    )

    new_password = ft.TextField(
        label="New Password",
        password=True,
        can_reveal_password=True,
        width=400
    )

    def save_new_password(e):
        selected_email = email_dropdown.value
        if not selected_email or not new_password.value:
            page.snack_bar = ft.SnackBar(ft.Text("Please select a user and enter a password"), open=True)
            page.update()
            return

        users = load_users()
        if selected_email in users:
            users[selected_email]["password"] = hash_password(new_password.value)
            save_users(users)

        from admin.user_management import user_management
        user_management(content, username)

    def go_back(e):
        from admin.user_management import user_management
        user_management(content, username)

    form_column = ft.Column(
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
        spacing=15,
        horizontal_alignment=ft.CrossAxisAlignment.START,
    )

    content.controls.append(
        ft.Row(
            controls=[
                ft.Container(
                    content=form_column,
                    padding=20,
                )
            ],
            alignment=ft.MainAxisAlignment.CENTER,
            expand=True
        )
    )
    content.update()
