import flet as ft
from typing import Optional
import json
import os
import hashlib
from admin.utils.team_utils import get_team_options
from utils.session_logger import log_activity

USERS_FILE = "data/users.json"

def hash_password(password: str) -> str:
    """Convert password to a SHA-256 hash."""
    return hashlib.sha256(password.encode()).hexdigest()

def add_user_hybrid_page(content: ft.Column, page: ft.Page, username: Optional[str], hybrid_app):
    """
    Enhanced Add User form with hybrid backend support
    """
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
                f"{'Adding to NAS Database' if hybrid_app else 'Adding to Local Files'}",
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
                    users[user['email']] = user
                
                print(f"👥 Hybrid: Loaded {len(users)} users")
                return users
                
            except Exception as e:
                print(f"⚠️ Error loading hybrid users: {e}")
        
        # Ensure users.json exists for legacy
        if not os.path.exists(USERS_FILE):
            os.makedirs(os.path.dirname(USERS_FILE), exist_ok=True)
            with open(USERS_FILE, "w") as f:
                json.dump({}, f)
        
        with open(USERS_FILE, "r") as f:
            users = json.load(f)
        
        print(f"👥 Legacy: Loaded {len(users)} users")
        return users

    def save_user(user_email: str, user_data: dict):
        """Save user to hybrid or legacy system"""
        if hybrid_app:
            try:
                # Create user in hybrid backend
                result = hybrid_app.user_service.create_user(user_data)
                if result:
                    # Log activity
                    hybrid_app.activity_service.log_activity(
                        username, 
                        f"Added new user '{user_data['username']}' with role '{user_data['role']}'"
                    )
                    print(f"✅ Hybrid: User {user_email} created")
                    return True
                else:
                    print(f"⚠️ Hybrid: Failed to create user {user_email}")
                    return False
                    
            except Exception as e:
                print(f"⚠️ Error saving to hybrid: {e}")
                # Fallback to legacy
                return save_user_legacy(user_email, user_data)
        else:
            return save_user_legacy(user_email, user_data)

    def save_user_legacy(user_email: str, user_data: dict):
        """Legacy user save"""
        try:
            users = load_users()
            users[user_email] = user_data
            
            with open(USERS_FILE, "w") as f:
                json.dump(users, f, indent=4)
            
            # Log activity
            log_activity(username, f"Added new user '{user_data['username']}' with role '{user_data['role']}'")
            
            print(f"✅ Legacy: User {user_email} saved")
            return True
        except Exception as e:
            print(f"❌ Error saving user to legacy: {e}")
            return False

    def get_team_options_enhanced():
        """Get team options from hybrid or legacy system"""
        if hybrid_app:
            try:
                teams = hybrid_app.team_service.get_teams()
                return [ft.dropdown.Option(team) for team in teams]
            except Exception as e:
                print(f"⚠️ Error loading hybrid teams: {e}")
        
        # Fallback to legacy
        return [ft.dropdown.Option(opt) for opt in get_team_options()]

    # Form fields with enhanced styling
    fullname = ft.TextField(
        label="Full Name",
        width=400,
        border_radius=10,
        helper_text="Enter the user's full name"
    )
    
    email = ft.TextField(
        label="Email",
        width=400,
        border_radius=10,
        helper_text="This will be used as the unique identifier"
    )
    
    username_field = ft.TextField(
        label="Username",
        width=400,
        border_radius=10,
        helper_text="Username for login purposes"
    )
    
    password = ft.TextField(
        label="Password",
        password=True,
        can_reveal_password=True,
        width=400,
        border_radius=10,
        helper_text="Minimum 6 characters recommended"
    )
    
    role = ft.Dropdown(
        label="Role",
        width=400,
        options=[
            ft.dropdown.Option("ADMIN"),
            ft.dropdown.Option("TEAM_LEADER"),
            ft.dropdown.Option("USER")
        ],
        value="USER",
        helper_text="Select the user's access level"
    )

    # Enhanced team dropdown with multi-select capability
    team_dropdown = ft.Dropdown(
        label="Primary Team",
        width=400,
        options=get_team_options_enhanced(),
        helper_text="Select the user's primary team"
    )

    # Additional team chips (for future multi-team support)
    selected_teams = ft.Row(spacing=5, wrap=True)

    # Validation and save functions
    def validate_form():
        """Validate form inputs"""
        errors = []
        
        if not fullname.value or not fullname.value.strip():
            errors.append("Full Name is required")
        
        if not email.value or not email.value.strip():
            errors.append("Email is required")
        elif "@" not in email.value:
            errors.append("Email must be a valid email address")
        
        if not username_field.value or not username_field.value.strip():
            errors.append("Username is required")
        
        if not password.value or len(password.value) < 6:
            errors.append("Password must be at least 6 characters long")
        
        if not role.value:
            errors.append("Role must be selected")
        
        return errors

    def check_user_exists(email_val: str, username_val: str):
        """Check if user already exists"""
        users = load_users()
        
        if email_val in users:
            return f"User with email '{email_val}' already exists"
        
        for existing_email, user_data in users.items():
            if user_data.get('username', '').lower() == username_val.lower():
                return f"User with username '{username_val}' already exists"
        
        return None

    def save_user_action(e):
        """Save the new user"""
        # Validate form
        validation_errors = validate_form()
        if validation_errors:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"Validation Error: {', '.join(validation_errors)}"),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return

        # Check if user exists
        email_val = email.value.strip().lower()
        username_val = username_field.value.strip()
        
        exists_error = check_user_exists(email_val, username_val)
        if exists_error:
            page.snack_bar = ft.SnackBar(
                content=ft.Text(exists_error),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()
            return

        # Prepare user data
        hashed_pw = hash_password(password.value)
        user_data = {
            "email": email_val,
            "fullname": fullname.value.strip(),
            "username": username_val,
            "password": hashed_pw,
            "role": role.value,
            "team_tags": [team_dropdown.value] if team_dropdown.value else [],
            "created_at": "2025-08-11",  # Current date
            "created_by": username
        }

        # Save user
        success = save_user(email_val, user_data)
        
        if success:
            # Show success message
            page.snack_bar = ft.SnackBar(
                content=ft.Text(f"User '{username_val}' created successfully!"),
                bgcolor=ft.Colors.GREEN
            )
            page.snack_bar.open = True
            page.update()
            
            # Return to user management after short delay
            import threading
            threading.Timer(1.5, lambda: go_back(None)).start()
        else:
            # Show error message
            page.snack_bar = ft.SnackBar(
                content=ft.Text("Failed to create user. Please try again."),
                bgcolor=ft.Colors.RED
            )
            page.snack_bar.open = True
            page.update()

    def go_back(e):
        """Return to user management"""
        if hybrid_app:
            from admin.user_management_hybrid import user_management_hybrid
            content.controls.clear()
            user_management_hybrid(content, username, hybrid_app)
        else:
            from admin.user_management import user_management
            content.controls.clear()
            user_management(content, username)

    # Enhanced form layout with better styling
    form_column = ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.PERSON_ADD, size=32, color=ft.Colors.BLUE),
            ft.Text("Add New User", size=24, weight="bold")
        ], spacing=15),
        
        ft.Divider(),
        
        # Personal Information Section
        ft.Text("Personal Information", size=18, weight="bold", color=ft.Colors.BLUE),
        fullname,
        email,
        
        ft.Container(height=10),
        
        # Account Information Section
        ft.Text("Account Information", size=18, weight="bold", color=ft.Colors.BLUE),
        username_field,
        password,
        
        ft.Container(height=10),
        
        # Access Control Section
        ft.Text("Access Control", size=18, weight="bold", color=ft.Colors.BLUE),
        role,
        team_dropdown,
        
        ft.Container(height=20),
        
        # Action buttons
        ft.Row([
            ft.ElevatedButton(
                "Save User",
                icon=ft.Icons.SAVE,
                on_click=save_user_action,
                style=ft.ButtonStyle(
                    bgcolor={ft.ControlState.DEFAULT: ft.Colors.GREEN,
                             ft.ControlState.HOVERED: ft.Colors.GREEN_700},
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
        width=500
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

    content.update()