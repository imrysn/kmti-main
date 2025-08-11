import flet as ft
import json
import os
import hashlib
from utils.auth import validate_login
from admin_panel import admin_panel
from user.user_panel import user_panel
from flet import FontWeight, CrossAxisAlignment, MainAxisAlignment
from utils.session_logger import log_login
from datetime import datetime


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

SESSION_ROOT = r"\\KMTI-NAS\Shared\data\session"


def save_session(username: str, role: str, panel: str):
    """
    Save session per user including which panel was opened and login_time.
    panel should be 'admin' or 'user'.
    """
    safe_name = safe_username_for_file(username)
    user_session_dir = os.path.join(SESSION_ROOT, safe_name)
    os.makedirs(user_session_dir, exist_ok=True)
    session_file = os.path.join(user_session_dir, "session.json")
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
    """Clear session per user (on explicit logout)."""
    safe_name = safe_username_for_file(username)
    session_file = os.path.join(SESSION_ROOT, safe_name, "session.json")
    try:
        if os.path.exists(session_file):
            os.remove(session_file)
            print(f"[DEBUG] Cleared session for {username}")
    except Exception as ex:
        print(f"[DEBUG] clear_session error: {ex}")


def _read_session_file(path: str) -> dict | None:
    """Safely read a session file and return dict or None."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"[DEBUG] Failed to read session file {path}: {e}")
        return None


def check_existing_session(page: ft.Page):
    """
    Find the most-recent session file under session/*/session.json and open its recorded panel.
    Returns True if it opened a panel, False otherwise.
    """
    if not os.path.exists(SESSION_ROOT):
        return False

    best = None  # tuple (timestamp, data)
    for user_folder in os.listdir(SESSION_ROOT):
        session_file = os.path.join(SESSION_ROOT, user_folder, "session.json")
        if not os.path.exists(session_file):
            continue
        data = _read_session_file(session_file)
        if not isinstance(data, dict):
            continue

        # prefer explicit login_time in session, else file mtime
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
    role = session_data.get("role", "")
    panel = session_data.get("panel")  # 'admin' or 'user' if present

    # prefer explicit panel saved in session; otherwise fallback to role
    try:
        if panel:
            panel = panel.lower()
            if panel == "admin":
                admin_panel(page, username)
            else:
                user_panel(page, username)
            print(f"[DEBUG] Auto-restored session for {username} -> panel={panel}")
            return True
        else:
            # fallback by role
            if isinstance(role, str) and role.upper() == "ADMIN":
                admin_panel(page, username)
            else:
                user_panel(page, username)
            print(f"[DEBUG] Auto-restored session for {username} by role={role}")
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

    # If there's an active session, auto-restore the most recent one
    if check_existing_session(page):
        return

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

    def login_action(e):
        nonlocal saved_credentials
        saved_credentials = load_saved_credentials()
        saved_usernames.clear()
        if isinstance(saved_credentials, dict):
            saved_usernames.extend(saved_credentials.keys())

        uname = (username.value or "").strip()
        pwd = password.value or ""

        role = validate_login(uname, pwd, is_admin_login)
        error_text.value = ""

        if role in ["ADMIN", "USER"]:
            if is_admin_login and role != "ADMIN":
                error_text.value = f"Access denied: This account is for '{role}' only!"
                page.update()
                return

            # Log & runtime reset
            log_login(uname, role)
            reset_runtime_start(uname)

            # Remember-me handling
            if remember_me.value:
                try:
                    os.makedirs("data", exist_ok=True)
                    saved_credentials[uname] = {
                        "password": hash_password(pwd),
                        "role": role
                    }
                    with open("data/remember_me.json", "w", encoding="utf-8") as f:
                        json.dump(saved_credentials, f, indent=4)
                    page.snack_bar = success_snackbar
                    page.snack_bar.open = True
                    page.update()
                except Exception as ex:
                    print(f"[DEBUG] remember_me write error: {ex}")

            # Determine which panel we're actually opening right now
            panel_to_open = "admin" if is_admin_login else "user"

            # Save session including panel and timestamp
            try:
                save_session(uname, role, panel_to_open)
            except Exception as ex:
                print(f"[DEBUG] save_session error: {ex}")

            # Navigate to chosen panel
            page.clean()
            if panel_to_open == "admin":
                admin_panel(page, uname)
            else:
                user_panel(page, uname)

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

    page.controls.clear()
    page.add(main_column)
    page.update()
