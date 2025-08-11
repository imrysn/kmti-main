import flet as ft
import json
import os
import hashlib
from typing import Optional
from utils.session_logger import log_activity

USERS_FILE = "data/users.json"

def hash_password(password: str) -> str:
    """Convert password to a SHA-256 hash."""
    return hashlib.sha256(password.encode()).hexdigest()

def reset_password_hybrid_page(content: ft.Column, page: ft.Page, admin_username: Optional[str], hybrid_app):
    """Enhanced reset password UI with hybrid backend support"""
    content.controls.clear()

    # System status header
    system_status = ft.Container(
        content=ft.Row([
            ft.Icon(
                ft.Icons.CLOUD_DONE if hybrid_app else ft.Icons.FOLDER, 
                color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                size=16
            ),
            ft.Text(
                f"{'Resetting in NAS Database' if hybrid_app else 'Resetting in Local Files'}",
                size=12,
                color=ft.Colors.GREEN if hybrid_app else ft.Colors.ORANGE,
                weight=ft.FontWeight.BOLD
            )
        ], spacing=5),
        bgcolor=ft.Colors.GREEN_100 if hybrid_app else ft.Colors.ORANGE_100,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        border_radius=10,
        margin=ft.margin.only(bottom=20)
    )

    def load_users():
        """Load users from hybrid or legacy system"""
        if hybrid_app:
            try:
                # Get users from hybrid backend
                hybrid_users = hybrid_app.user_service.get_users()
                
                # Convert to legacy format for compatibility
                users = {}
                for user in hybrid_users:
                    users[user['email']] = {
                        'fullname': user.get('fullname', ''),
                        'username': user.get('username', ''),
                        'role': user.get('role', 'USER'),
                        'team_tags': user.get('team_tags', [])
                    }
                
                print(f"👥 Hybrid: Loaded {len(users)} users for password reset")
                return users
                
            except Exception as e:
                print(f"⚠️ Error loading hybrid users: {e}")
        
        # Fallback to legacy
        if not os.path.exists(USERS_FILE):
            return {}
        
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        
        print(f"👥 Legacy: Loaded {len(users)} users for password reset")
        return users

    def reset_user_password(user_email: str, new_password: str):
        """Reset user password in hybrid or legacy system"""
        if hybrid_app:
            try:
                # Update password in hybrid backend
                user_data = {'password': hash_password(new_password)}
                result = hybrid_app.user_service.update_user(user_email, user_data)
                
                if result:
                    # Log activity
                    hybrid_app.activity_service.log_activity(
                        admin_username, 
                        f"Reset password for user {user_email}"
                    )
                    print(f"✅ Hybrid: Password reset for {user_email}")
                    return True
                else:
                    print(f"⚠️ Hybrid: Failed to reset password for {user_email}")
                    return False
                    
            except Exception as e:
                print(f"⚠️ Error resetting password in hybrid: {e}")
                # Fallback to legacy
                return reset_password_legacy(user_email, new_password)
        else:
            return reset_password_legacy(user_email, new_password)

    def reset_password_legacy(user_email: str, new_password: str):
        """Legacy password reset"""
        try:
            users = load_users()
            if user_email in users:
                users[user_email]["password"] = hash_password(new_password)
                
                with open(USERS_FILE, "w") as f:
                    json.dump(users, f, indent=4)

                # Log activity
                log_activity(admin_username, f"Reset password for user {user_email}")
                
                print(f"✅ Legacy: Password reset for {user_email}")
                return True
            else:
                print(f"⚠️ Legacy: User {user_email} not found")
                return False
                
        except Exception as e:
            print(f"❌ Error resetting password in legacy: {e}")
            return False

    # Load users and create dropdown options
    users = load_users()
    
    # Enhanced user dropdown with user info
    user_options = []
    for email, user_data in users.items():
        fullname = user_data.get('fullname', 'Unknown')
        username = user_data.get('username', 'unknown')
        role = user_data.get('role', 'USER')
        
        # Create display text with user info
        display_text = f"{fullname} ({username}) - {role}"
        user_options.append(ft.dropdown.Option(key=email, text=display_text))

    email_dropdown = ft.Dropdown(
        label="Select User to Reset Password",
        width=500,
        options=user_options,
        helper_text="Choose the user whose password you want to reset"
    )

    # Enhanced password fields
    new_password = ft.TextField(
        label="New Password",
        password=True,
        can_reveal_password=True,
        width=500,
        helper_text="Minimum 6 characters recommended"
    )

    confirm_password = ft.TextField(
        label="Confirm New Password",
        password=True,
        can_reveal_password=True,
        width=500,
        helper_text="Re-enter the new password to confirm"
    )

    # Selected user info display
    user_info_container = ft.Container(
        visible=False,
        bgcolor=ft.Colors.BLUE_50,
        border_radius=10,
        padding=15,
        margin=ft.margin.only(top=10, bottom=10)
    )

    def on_user_selected(e):
        """Display selected user information"""
        selected_email = email_dropdown.value
        if selected_email and selected_email in users:
            user_data = users[selected_email]
            
            user_info = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.PERSON, color=ft.Colors.BLUE),
                    ft.Text("Selected User Information", weight=ft.FontWeight.BOLD, color=ft.Colors.BLUE)
                ], spacing=10),
                ft.Text(f"Full Name: {user_data.get('fullname', 'Unknown')}", size=14),
                ft.Text(f"Email: {selected_email}", size=14),
                ft.Text(f"Username: {user_data.get('username', 'unknown')}", size=14),
                ft.Text(f"Role: {user_data.get('role', 'USER')}", size=14),
                ft.Text(f"Teams: {', '.join(user_data.get('team_tags', [])) if user_data.get('team_tags') else 'No teams'}", size=14),
            ], spacing=5)
            
            user_info_container.content = user_info
            user_info_container.visible = True
        else:
            user_info_container.visible = False
        
        page.update()

    email_dropdown.on_change = on_user_selected

    def validate_passwords():
        """Validate password inputs"""
        if not new_password.value or len(new_password.value) < 6:
            return "Password must be at least 6 characters long"
        
        if new_password.value != confirm_password.value:
            return "Passwords do not match"
        
        return None

    def save_new_password(e):
        """Save the new password"""
        selected_email = email_dropdown.value
        
        if not selected_email:
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Please select a user"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return

        # Validate passwords
        password_error = validate_passwords()
        if password_error:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(password_error),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return

        # Reset password
        success = reset_user_password(selected_email, new_password.value)
        
        if success:
            # Show success message
            user_data = users.get(selected_email, {})
            username = user_data.get('username', 'Unknown')
            
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Password reset successfully for user '{username}'!"),
                bgcolor=ft.Colors.GREEN
            )
            page.snack_bar.open = True
            page.update()
            
            # Return to user management after short delay
            import threading
            threading.Timer(2.0, lambda: go_back(None)).start()
        else:
            # Show error message
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Failed to reset password. Please try again."),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()

    def go_back(e):
        """Return to user management"""
        if hybrid_app:
            from admin.user_management import user_management
            content.controls.clear()
            user_management(content, admin_username)
        else:
            from admin.user_management import user_management
            content.controls.clear()
            user_management(content, admin_username)

    # Enhanced form layout
    form_column = ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.LOCK_RESET, size=32, color=ft.Colors.ORANGE),
            ft.Text("Reset User Password", size=24, weight="bold")
        ], spacing=15),
        
        ft.Divider(),
        
        # User Selection Section
        ft.Text("Select User", size=18, weight="bold", color=ft.Colors.BLUE),
        ft.Text("Choose the user whose password you want to reset", size=12, color=ft.Colors.GREY_600),
        email_dropdown,
        user_info_container,
        
        ft.Container(height=10),
        
        # Password Section
        ft.Text("New Password", size=18, weight="bold", color=ft.Colors.BLUE),
        ft.Text("Enter and confirm the new password", size=12, color=ft.Colors.GREY_600),
        new_password,
        confirm_password,
        
        ft.Container(height=20),
        
        # Action buttons
        ft.Row([
            ft.ElevatedButton(
                "Reset Password",
                icon=ft.Icons.SAVE,
                on_click=save_new_password,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.ORANGE,
                             ft.ControlState.HOVERED: ft.Colors.ORANGE_700},
                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                    padding=ft.padding.symmetric(horizontal=25, vertical=12),
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            ),
            ft.ElevatedButton(
                "Cancel",
                icon=ft.Icons.CANCEL,
                on_click=go_back,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREY_400,
                             ft.ControlState.HOVERED: ft.Colors.GREY_600},
                    color={ft.ControlState.DEFAULT: ft.Colors.WHITE,
                           ft.ControlState.HOVERED: ft.Colors.WHITE},
                    padding=ft.padding.symmetric(horizontal=25, vertical=12),
                    shape=ft.RoundedRectangleBorder(radius=8)
                )
            ),
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=20),
    ], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15)

    # Main container with enhanced styling
    main_container = ft.Container(
        content=form_column,
        padding=30,
        bgcolor=ft.Colors.WHITE,
        border_radius=15,
        shadow=ft.BoxShadow(
            blur_radius=10,
            spread_radius=2,
            color=ft.Colors.with_opacity(0.1, ft.Colors.BLACK)
        ),
        width=600
    )

    # Centered layout
    content.controls.extend([
        system_status,
        ft.Row([
            ft.Container(expand=True),
            main_container,
            ft.Container(expand=True)
        ], alignment=ft.MainAxisAlignment.CENTER, expand=True)
    ])

    page.update()