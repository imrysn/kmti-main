import flet as ft
import json
import os
import hashlib
from utils.auth import validate_login
from admin_panel import admin_panel
from user_panel import user_panel
from flet import FontWeight, CrossAxisAlignment, MainAxisAlignment
from typing import Optional

def hash_password(password: str | None) -> str:
    if password is None:
        return ""
    return hashlib.sha256(password.encode()).hexdigest()

def load_saved_credentials():
    if os.path.exists("data/remember_me.json"):
        with open("data/remember_me.json", "r") as f:
            return json.load(f)
    return {}

def login_view(page: ft.Page):
    page.title = "KMTI Data Management Login"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = "#D9D9D9"

    is_admin_login = False

    # Load saved credentials (all remembered users)
    saved_credentials = load_saved_credentials()
    saved_usernames = list(saved_credentials.keys()) if isinstance(saved_credentials, dict) else []

    username = ft.TextField(
        label="Username",
        width=300,
        border_radius=10,
        height=50,
        border_color="#cccccc",
        focused_border_color="#000000",
        bgcolor=ft.Colors.WHITE,
    )

    password = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=300,
        border_radius=10,
        height=50,
        border_color="#cccccc",
        focused_border_color="#000000",
        bgcolor=ft.Colors.WHITE
    )

    remember_me = ft.Checkbox(label="Remember Me", value=False)
    error_text = ft.Text("", color="red")
    login_type_text = ft.Text("USER", size=18, weight=FontWeight.W_500)
    success_snackbar = ft.SnackBar(content=ft.Text("Password remembered successfully!"))

    def login_action(e):
        nonlocal saved_credentials
        saved_credentials = load_saved_credentials()
        saved_usernames.clear()
        if isinstance(saved_credentials, dict):
            saved_usernames.extend(saved_credentials.keys())

        role = validate_login(username.value, password.value, is_admin_login)
        error_text.value = ""

        if role in ["admin", "user"]:
            expected_role = "admin" if is_admin_login else "user"
            if role != expected_role:
                error_text.value = f"Access denied: This account is for '{role.upper()}' only!"
                page.update()
                return

            # Save if remember me is checked
            if remember_me.value:
                os.makedirs("data", exist_ok=True)
                saved_credentials[username.value] = {
                    "password": hash_password(password.value),
                    "role": role
                }
                with open("data/remember_me.json", "w") as f:
                    json.dump(saved_credentials, f, indent=4)
                page.snack_bar = success_snackbar
                page.snack_bar.open = True
                page.update()

            page.clean()
            if role == "admin":
                admin_panel(page, username.value)
            else:
                user_panel(page, username.value)
        else:
            error_text.value = "Invalid credentials!"
            page.update()

    def toggle_login_type(e):
        nonlocal is_admin_login
        is_admin_login = not is_admin_login
        login_type_text.value = "ADMINISTRATOR" if is_admin_login else "USER"
        login_type_switch.content.value = (
            "Login as User" if is_admin_login else "Login as Administrator"
        )
        page.update()

    reset_password = ft.Text(
        "Reset password", color="#000000", weight=FontWeight.W_500, size=12
    )

    login_type_switch = ft.TextButton(
        content=ft.Text("Login as Administrator", color="#000000", size=12),
        on_click=toggle_login_type
    )

    login_card = ft.Card(
        elevation=5,
        content=ft.Container(
            width=400,
            padding=40,
            bgcolor=ft.Colors.with_opacity(0.8, ft.Colors.GREY_400),
            border_radius=10,
            content=ft.Column(
                [
                    login_type_text,
                    ft.Divider(height=20, color="transparent"),
                    username,
                    password,
                    remember_me,
                    ft.Divider(height=10, color="transparent"),
                    ft.ElevatedButton(
                        "Login",
                        on_click=login_action,
                        width=150,
                        height=45,
                        style=ft.ButtonStyle(
                            shape=ft.RoundedRectangleBorder(radius=10),
                            bgcolor={ft.ControlState.DEFAULT: ft.Colors.BLACK,
                                     ft.ControlState.HOVERED: ft.Colors.WHITE},
                            side={ft.ControlState.HOVERED: ft.BorderSide(1, ft.Colors.BLACK)},
                            color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                                   ft.ControlState.HOVERED: ft.Colors.BLACK}
                        )
                    ),
                    reset_password,
                    error_text,
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=5
            )
        )
    )

    main_column = ft.Column(
        [
            ft.Image(src="assets/kmti_logo.png", width=150),
            ft.Divider(height=30, color="transparent"),
            login_card,
            ft.Divider(height=20, color="transparent"),
            login_type_switch
        ],
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=0
    )

    page.add(main_column)
