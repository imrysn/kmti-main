import flet as ft
import json
import os
import hashlib
from utils.auth import validate_login
from admin_panel import admin_panel
from user.user_panel import user_panel
from flet import FontWeight, CrossAxisAlignment, MainAxisAlignment
from typing import Optional
from utils.session_logger import log_login
from datetime import datetime


def hash_password(password: str | None) -> str:
    if password is None:
        return ""
    return hashlib.sha256(password.encode()).hexdigest()


def load_saved_credentials():
    if os.path.exists("data/remember_me.json"):
        with open("data/remember_me.json", "r") as f:
            return json.load(f)
    return {}


def reset_runtime_start(username: str):
    """Reset runtime_start to now for the given username."""
    users_file = "data/users.json"
    if not os.path.exists(users_file):
        return
    try:
        with open(users_file, "r") as f:
            users = json.load(f)
    except Exception:
        return

    now = datetime.now().isoformat()
    for email, data in users.items():
        if data.get("username") == username:
            data["runtime_start"] = now
            break

    with open(users_file, "w") as f:
        json.dump(users, f, indent=4)


def login_view(page: ft.Page):
    page.title = "KMTI Data Management Login"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = "#D9D9D9"

    is_admin_login = False
    saved_credentials = load_saved_credentials()
    saved_usernames = list(saved_credentials.keys()) if isinstance(saved_credentials, dict) else []

    username = ft.TextField(
        label="Username", width=300, border_radius=10, height=50,
        border_color="#cccccc", focused_border_color="#000000", bgcolor=ft.Colors.WHITE,
    )

    password = ft.TextField(
        label="Password", password=True, can_reveal_password=True, width=300,
        border_radius=10, height=50, border_color="#cccccc",
        focused_border_color="#000000", bgcolor=ft.Colors.WHITE
    )

    remember_me = ft.Checkbox(label="Remember Me", value=False)
    error_text = ft.Text("", color="red")
    login_type_text = ft.Text("USER", size=18, weight=FontWeight.W_500)
    success_snackbar = ft.SnackBar(content=ft.Text("Password remembered successfully!"))

    def auto_login(username_val: str, role: str):
        """Handle automatic login for shortcut credentials"""
        # Log login action
        log_login(username_val, role)
        reset_runtime_start(username_val)
        
        # Clear the page and navigate
        page.clean()
        if role == "ADMIN":
            admin_panel(page, username_val)
        else:
            user_panel(page, username_val)

    def check_auto_login(username_val: str):
        """Check if username matches auto-login shortcuts"""
        if username_val.lower() == 'user acc':
            return True, "USER", "user_account"
        elif username_val.lower() == 'admin':
            return True, "ADMIN", "admin_account"
        return False, None, None

    def login_action(e):
        nonlocal saved_credentials
        saved_credentials = load_saved_credentials()
        saved_usernames.clear()
        if isinstance(saved_credentials, dict):
            saved_usernames.extend(saved_credentials.keys())

        # Check for auto-login shortcuts first
        is_auto, auto_role, auto_username = check_auto_login(username.value)
        if is_auto:
            auto_login(auto_username, auto_role)
            return

        role = validate_login(username.value, password.value, is_admin_login)
        error_text.value = ""

        if role in ["ADMIN", "USER"]:
            if is_admin_login:
                # Admin login page: must be ADMIN only
                if role != "ADMIN":
                    error_text.value = f"Access denied: This account is for '{role}' only!"
                    page.update()
                    return
            # Log login action
            log_login(username.value, role)
            reset_runtime_start(username.value)

            # Save credentials if remember me is checked
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

            # Navigation
            page.clean()
            if is_admin_login:
                # Admin login page always goes to admin panel
                admin_panel(page, username.value)
            else:
                # User login page: both ADMIN and USER go to user panel
                user_panel(page, username.value)

        else:
            error_text.value = "Invalid credentials!"
            page.update()

    def on_username_submit(e):
        """Handle Enter key press in username field"""
        # Check for auto-login shortcuts
        is_auto, auto_role, auto_username = check_auto_login(username.value)
        if is_auto:
            auto_login(auto_username, auto_role)
        else:
            # If not auto-login, focus on password field
            password.focus()

    def on_password_submit(e):
        """Handle Enter key press in password field"""
        login_action(e)

    # Add submit handlers to text fields
    username.on_submit = on_username_submit
    password.on_submit = on_password_submit

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