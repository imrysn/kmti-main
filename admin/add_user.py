import flet as ft
from typing import Optional
import json
import os
import hashlib
from admin.utils.team_utils import get_team_options

USERS_FILE = "data/users.json"


def hash_password(password: str) -> str:
    """Convert password to a SHA-256 hash."""
    return hashlib.sha256(password.encode()).hexdigest()


def add_user_page(content: ft.Column, page: ft.Page, username: Optional[str]):
    """
    Renders the Add User form into the existing `content` column,
    leaving the navbar intact.
    """
    content.controls.clear()

    # Ensure users.json exists
    if not os.path.exists(USERS_FILE):
        os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
        with open(USERS_FILE, "w") as f:
            json.dump({}, f)

    def load_users():
        with open(USERS_FILE, "r") as f:
            return json.load(f)

    def save_users(users):
        with open(USERS_FILE, "w") as f:
            json.dump(users, f, indent=4)

    # Form fields
    fullname = ft.TextField(label="Full Name")
    email = ft.TextField(label="Email")
    username_field = ft.TextField(label="Username")
    password = ft.TextField(label="Password", password=True, can_reveal_password=True)
    role = ft.Dropdown(
        label="Role",
        options=[ft.dropdown.Option("ADMIN"), ft.dropdown.Option("USER")],
        value="USER",
    )

    team_dropdown = ft.Dropdown(
        label="Team",
        options=[ft.dropdown.Option(opt) for opt in get_team_options()]
    )

    # Actions
    def save_user(e):
        # Validation: required fields
        if not all([fullname.value, email.value, username_field.value, password.value, role.value]):
            page.snack_bar = ft.SnackBar(ft.Text("All fields except Team are required."), open=True)
            page.update()
            return

        users = load_users()

        # Hash the password before storing
        hashed_pw = hash_password(password.value)

        users[email.value] = {
            "fullname": fullname.value,
            "username": username_field.value,
            "password": hashed_pw,
            "role": role.value,
            "team_tags": [team_dropdown.value] if team_dropdown.value else [],
            "join_date": "2025-07-28",
        }
        save_users(users)

        # Go back to user management after saving
        from admin.user_management import user_management
        content.controls.clear()
        user_management(content, username)

    def go_back(e):
        from admin.user_management import user_management
        content.controls.clear()
        user_management(content, username)

    # Layout with horizontal margin
    content.controls.append(
        ft.Container(
            content=ft.Column(
                [
                    ft.Text("Add New User", size=24, weight="bold"),
                    fullname,
                    email,
                    username_field,
                    password,
                    role,
                    team_dropdown,
                    ft.Row(
                        [
                            ft.ElevatedButton("Save", 
                                              on_click=save_user,
                                              style=ft.ButtonStyle(
                                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                                                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                                              ft.ControlState.HOVERED: ft.Colors.BLACK},
                                                    side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK)},
                                                    shape=ft.RoundedRectangleBorder(radius=5)
                                                              )
                                              ),
                            ft.ElevatedButton("Back", 
                                              on_click=go_back,
                                              style=ft.ButtonStyle(
                                                  bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                                                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                                              ft.ControlState.HOVERED: ft.Colors.BLACK},
                                                    side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK)},
                                                    shape=ft.RoundedRectangleBorder(radius=5)
                                                              )),
                        ],
                        alignment=ft.MainAxisAlignment.CENTER,
                    ),
                ],
                horizontal_alignment=ft.CrossAxisAlignment.START,
                tight=True,
                spacing=15,
            ),
            alignment=ft.alignment.center,
            expand=True,
            margin=ft.margin.only(left=400, right=400, top=20),  
        )
    )

    content.update()
