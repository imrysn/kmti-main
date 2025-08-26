import flet as ft
import json
import os
import sys
import hashlib
from utils.auth import validate_login
from admin_panel import admin_panel
from user.user_panel import user_panel
from TLPanel import TLPanel
from flet import FontWeight, CrossAxisAlignment, MainAxisAlignment
from utils.session_logger import log_login, log_activity, log_panel_access
from datetime import datetime
from utils.windows_admin_access import check_admin_elevation_on_login

# -------------------------
# Resource Helper
# -------------------------

def resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and PyInstaller."""
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)

# -------------------------
# Utility Functions
# -------------------------

def hash_password(password: str | None) -> str:
    if password is None:
        return ""
    return hashlib.sha256(password.encode()).hexdigest()

def load_saved_credentials():
    if os.path.exists("data/remember_me.json"):
        try:
            with open("data/remember_me.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def reset_runtime_start(username: str):
    """Reset runtime_start to now for the given username."""
    users_file = "data/users.json"
    if not os.path.exists(users_file):
        return
    try:
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
    except Exception:
        return

    now = datetime.now().isoformat()
    for email, data in users.items():
        if data.get("username") == username:
            data["runtime_start"] = now
            break

    try:
        with open(users_file, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=4)
    except Exception:
        pass

def safe_username_for_file(username: str) -> str:
    """Return a filename-safe username."""
    return "".join(c for c in (username or "") if c.isalnum() or c in ("-", "_")).strip() or "user"

# -------------------------
# Session functions
# -------------------------

SESSION_ROOT = "data/sessions"  # Use consistent path

def save_session(username: str, role: str, panel: str):
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_ROOT, f"{safe_name}.json")
    os.makedirs(SESSION_ROOT, exist_ok=True)
    session_payload = {
        "username": username,
        "role": role,
        "panel": panel,
        "login_time": datetime.utcnow().isoformat()
    }
    try:
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(session_payload, f, indent=4)
        print(f"[DEBUG] Saved session for {username} (panel={panel}) -> {session_file}")
    except Exception as ex:
        print(f"[DEBUG] save_session error: {ex}")

def clear_session(username: str):
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_ROOT, f"{safe_name}.json")
    try:
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"[DEBUG] Cleared session for {username}")
    except Exception as ex:
        print(f"[DEBUG] clear_session error: {ex}")

def _read_session_file(path: str) -> dict | None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[DEBUG] Failed to read session file {path}: {e}")
        return None

def check_existing_session(page: ft.Page):
    if not os.path.exists(SESSION_ROOT):
        return False

    best = None
    for user_folder in os.listdir(SESSION_ROOT):
        session_file = os.path.join(SESSION_ROOT, user_folder, "session.json")
        if not os.path.exists(session_file):
            continue
        data = _read_session_file(session_file)
        if not isinstance(data, dict):
            continue

        login_time = None
        if "login_time" in data:
            try:
                login_time = datetime.fromisoformat(data["login_time"])
            except Exception:
                login_time = None
        if login_time is None:
            try:
                login_time = datetime.fromtimestamp(os.path.getmtime(session_file))
            except Exception:
                login_time = datetime.min

        if best is None or login_time > best[0]:
            best = (login_time, data)

    if not best:
        return False

    _, session_data = best
    username = session_data.get("username")
    role = (session_data.get("role") or "").upper()
    # Normalize role string
    if role == "TEAM LEADER":
        role = "TEAM_LEADER"
    panel = session_data.get("panel", "").lower()

    try:
        if panel == "admin":
            if role == "ADMIN":
                admin_panel(page, username)
            elif role == "TEAM_LEADER":
                TLPanel(page, username) 
            else:
                return False
        else:
            # User panel - allow both USER and TEAM_LEADER roles
            if role in ["USER", "TEAM_LEADER"]:
                user_panel(page, username)
            elif role == "ADMIN":
                admin_panel(page, username)
            else:
                return False
        print(f"[DEBUG] Auto-restored session for {username} (role={role}, panel={panel})")
        return True
    except Exception as e:
        print(f"[DEBUG] Failed to restore session panel for {username}: {e}")
        return False

# -------------------------
# Login View
# -------------------------

def login_view(page: ft.Page):
    page.title = "KMTI Data Management Login"
    page.vertical_alignment = MainAxisAlignment.CENTER
    page.horizontal_alignment = CrossAxisAlignment.CENTER
    page.bgcolor = "#D9D9D9"

    if check_existing_session(page):
        return

    is_admin_login = False

    username = ft.TextField(
        label="Username", width=300, border_radius=10, height=50,
        border_color="#cccccc", focused_border_color="#000000", bgcolor=ft.Colors.WHITE,
    )

    password = ft.TextField(
        label="Password", password=True, can_reveal_password=True, width=300,
        border_radius=10, height=50, border_color="#cccccc",
        focused_border_color="#000000", bgcolor=ft.Colors.WHITE
    )

    error_text = ft.Text("", color="red")
    login_type_text = ft.Text("USER", size=18, weight=FontWeight.W_500, color=ft.Colors.BLACK)

    def login_action(e):
        uname = (username.value or "").strip()
        pwd = password.value or ""
        role = validate_login(uname, pwd, is_admin_login)
        error_text.value = ""

        if role in ["ADMIN", "TEAM_LEADER", "USER"]:
            if role == "ADMIN":
                print(f"[LOGIN] Admin login detected: {uname} ({role})")
                
                # Show loading message
                error_text.value = "Checking administrator access..."
                error_text.color = ft.Colors.BLUE
                page.update()
                
                try:
                    elevation_success, elevation_message = check_admin_elevation_on_login(uname, role)
                    
                    if not elevation_success:
                        error_text.value = f"Administrator access issue: {elevation_message}"
                        error_text.color = ft.Colors.ORANGE
                        page.update()
                        
                        # Still allow login but with warning
                        import time
                        time.sleep(2)  # Show message briefly
                        error_text.value = "Proceeding without elevation - some features may require manual processing"
                        error_text.color = ft.Colors.ORANGE
                        page.update()
                        time.sleep(2)
                    else:
                        error_text.value = elevation_message
                        error_text.color = ft.Colors.GREEN
                        page.update()
                        import time
                        time.sleep(1)  # Show success message briefly
                        
                except Exception as ex:
                    print(f"[LOGIN] Elevation check error: {ex}")
                    error_text.value = "Network path access check failed - proceeding to fallback path"
                    error_text.color = ft.Colors.ORANGE
                    page.update()
                    import time
                    time.sleep(2)
            
            elif role == "TEAM_LEADER":
                print(f"[LOGIN] Team Leader login detected: {uname} ({role})")
                
                # Show success message for Team Leader
                error_text.value = "Team Leader access confirmed"
                error_text.color = ft.Colors.GREEN
                page.update()
                import time
                time.sleep(1)  
            
            error_text.value = ""
            
            log_login(uname, role)
            reset_runtime_start(uname)

            try:
                save_session(uname, role, "admin" if is_admin_login else "user")
            except Exception as ex:
                print(f"[DEBUG] save_session error: {ex}")

            page.clean()
            
            # Route to appropriate panel based on role and login type
            if is_admin_login:
                # Administrator login window
                if role == "ADMIN":
                    admin_panel(page, uname)
                elif role == "TEAM_LEADER":
                    # Team Leader accessing via Admin login -> TL Panel
                    TLPanel(page, uname)
                    # Log which panel was accessed
                    log_panel_access(uname, role, "admin", "admin")
                elif role == "USER":
                    # Users can access admin login but get redirected to user panel
                    user_panel(page, uname)
                else:
                    error_text.value = "Invalid role for admin login!"
                    error_text.color = ft.Colors.RED
                    page.update()
                    return
            else:
                # User login window - Team Leaders get User Panel, others get their appropriate panels
                if role == "USER":
                    user_panel(page, uname)
                elif role == "ADMIN":
                    admin_panel(page, uname)
                elif role == "TEAM_LEADER":
                    # Team Leader accessing via User login -> User Panel for file upload/management
                    user_panel(page, uname)
                    # Log which panel was accessed
                    log_panel_access(uname, role, "user", "user")
                else:
                    error_text.value = "Invalid role!"
                    error_text.color = ft.Colors.RED 
                    page.update()
                    return

        else:
            error_text.value = "Invalid credentials!"
            page.update()

    username.on_submit = lambda e: password.focus()
    password.on_submit = login_action

    def toggle_login_type(e):
        nonlocal is_admin_login
        is_admin_login = not is_admin_login
        if is_admin_login:
            login_type_text.value = "ADMINISTRATOR"
            login_type_text.color = ft.Colors.BLACK
            login_type_switch.content.value = "Login as User"
        else:
            login_type_text.value = "USER"
            login_type_text.color = ft.Colors.BLACK
            login_type_switch.content.value = "Login as Administrator"
        page.update()

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
                    error_text,
                ],
                horizontal_alignment=CrossAxisAlignment.CENTER,
                spacing=5
            )
        )
    )

    page.add(
        ft.Column(
            [
                ft.Image(src=resource_path("assets/kmti_logo.png"), width=150),
                ft.Divider(height=30, color="transparent"),
                login_card,
                ft.Divider(height=20, color="transparent"),
                login_type_switch
            ],
            horizontal_alignment=CrossAxisAlignment.CENTER
        )
    )
    page.update()
