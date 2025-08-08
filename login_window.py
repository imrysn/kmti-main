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

def get_hybrid_app():
    """Get hybrid app instance from main module"""
    try:
        from main import get_hybrid_app_for_module
        return get_hybrid_app_for_module()
    except ImportError:
        return None

def hybrid_validate_login(username: str, password: str, is_admin_login: bool = False):
    """Enhanced login validation with hybrid backend support"""
    hybrid_app = get_hybrid_app()
    
    if hybrid_app:
        # Use hybrid authentication
        try:
            user = hybrid_app.user_service.authenticate(username, password)
            if user:
                role = user['role']
                
                # Check admin login restrictions
                if is_admin_login and role != "ADMIN":
                    return None  # Admin page requires ADMIN role
                
                return role
            else:
                return None
        except Exception as e:
            print(f"Hybrid authentication error: {e}")
            # Fall back to legacy authentication
            return validate_login(username, password, is_admin_login)
    else:
        # Use legacy authentication
        return validate_login(username, password, is_admin_login)

def reset_runtime_start(username: str):
    """Reset runtime_start to now for the given username - works with both systems"""
    hybrid_app = get_hybrid_app()
    
    if hybrid_app:
        # Hybrid system handles this automatically in authentication
        # But we can also update the legacy file for compatibility
        pass
    
    # Always update legacy file for backward compatibility
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

def hybrid_save_session(username: str, role: str):
    """Save session using hybrid system if available, otherwise legacy"""
    hybrid_app = get_hybrid_app()
    
    if hybrid_app:
        # Hybrid system already saves session during authentication
        # Session is automatically saved to local %APPDATA%/KMTI/session_{user}.json
        print(f"✅ Hybrid session saved for {username}")
    else:
        # Legacy session saving
        from user.user_panel import save_session
        panel_type = "admin" if role == "ADMIN" else "user"
        save_session(username, panel_type)
        print(f"✅ Legacy session saved for {username}")

def login_view(page: ft.Page):
    """Login view with hybrid backend integration - UI preserved exactly"""
    page.title = "KMTI Data Management Login"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = "#D9D9D9"

    is_admin_login = False
    saved_credentials = load_saved_credentials()
    saved_usernames = list(saved_credentials.keys()) if isinstance(saved_credentials, dict) else []

    # Show hybrid status (optional - you can remove this if you don't want it)
    hybrid_app = get_hybrid_app()
    system_status = "🌐 NAS Connected" if hybrid_app else "💽 Legacy Mode"
    print(f"Login system status: {system_status}")

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

    def login_action(e):
        """Enhanced login action with hybrid backend support"""
        nonlocal saved_credentials
        saved_credentials = load_saved_credentials()
        saved_usernames.clear()
        if isinstance(saved_credentials, dict):
            saved_usernames.extend(saved_credentials.keys())

        # Use hybrid validation instead of legacy
        role = hybrid_validate_login(username.value, password.value, is_admin_login)
        error_text.value = ""

        if role in ["ADMIN", "USER", "TEAM_LEADER"]:  # Added TEAM_LEADER support
            if is_admin_login:
                # Admin login page: must be ADMIN only
                if role != "ADMIN":
                    error_text.value = f"Access denied: This account is for '{role}' only!"
                    page.update()
                    return
            
            # Log login action (preserve your existing logging)
            log_login(username.value, role)
            reset_runtime_start(username.value)

            # Save credentials if remember me is checked (preserve existing functionality)
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

            # Save session using appropriate system
            hybrid_save_session(username.value, role)

            # Navigation (preserve your exact logic)
            page.clean()
            if is_admin_login:
                # Admin login page always goes to admin panel
                admin_panel(page, username.value)
            else:
                # User login page: ADMIN, TEAM_LEADER and USER go to user panel
                # But ADMIN can also access admin panel from user panel
                if role in ["ADMIN", "TEAM_LEADER"]:
                    # For admins and team leaders, we might want to go to admin panel
                    # But preserving your original logic
                    user_panel(page, username.value)
                else:
                    user_panel(page, username.value)

        else:
            error_text.value = "Invalid credentials!"
            page.update()

    def toggle_login_type(e):
        """Preserve your existing login type toggle functionality"""
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

    # Your exact login card design preserved
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

    # Your exact main layout preserved
    main_column = ft.Column(
        [
            ft.Image(src="assets/kmti_logo.png", width=150),
            ft.Divider(height=30, color="transparent"),
            login_card,
            ft.Divider(height=20, color="transparent"),
            login_type_switch,
            # Optional: Add subtle system status indicator (you can remove this)
            ft.Container(
                content=ft.Text(
                    system_status,
                    size=10,
                    color="#666666"
                ),
                margin=ft.margin.only(top=10)
            )
        ],
        horizontal_alignment=CrossAxisAlignment.CENTER,
        spacing=0
    )

    page.add(main_column)